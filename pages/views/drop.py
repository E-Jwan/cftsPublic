# ====================================================================
# core
import ast
import datetime
import shutil
import io
from django.contrib import messages
from django.core import paginator
from django.core.mail import EmailMessage
from django.core.files import File as DjangoFile
from zipfile import ZipFile
from django.utils import timezone
from cfts import settings as cftsSettings

# cryptography
import os
import string
import random
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# decorators
from django.contrib.auth.decorators import login_required, user_passes_test

from pages.views.auth import staffCheck, getOrCreateEmail
from pages.views.dev_tools import fileCleanup

# responses
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from django.http import FileResponse, HttpResponse

# model/database stuff
from pages.models import *

import logging

logger = logging.getLogger('django')

# function to collect Request objects and serve the transfer queue page, only available to staff users
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def dropZone(request):
    dropRequests = Drop_Request.objects.filter(user_retrieved=False).order_by('email_sent')

    requestPage = paginator.Paginator(dropRequests, 10)
    pageNum = request.GET.get('page')
    pageObj = requestPage.get_page(pageNum)
    return render(request, 'pages/drop-zone.html', context={'dropRequests': pageObj, 'debug': cftsSettings.DEBUG})

def treeScan(requestPaths, path):
    for dir in os.scandir(path):
        if dir.is_file():
            requestPaths.append(os.path.dirname(dir.path))
        else:
            treeScan(requestPaths, dir)
    return requestPaths

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def dropEmail(request, id):
    dropRequest = Drop_Request.objects.get(request_id=id)

    requestInfo = ast.literal_eval(dropRequest.request_info)

    keyPath = os.path.join(cftsSettings.KEYS_DIR, cftsSettings.NETWORK + "_PRIV_KEY.pem")
    with open(keyPath, "rb") as infile:
        privKey = load_pem_private_key(infile.read(), password=str.encode(cftsSettings.PRIVATE_KEY_PASSWORD, 'utf-8'))
        infile.close()

    decryptedPhrase = privKey.decrypt(requestInfo['encryptedPhrase'], padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None)).decode()

    url = str(request.get_host()) + "/drop/" + str(id)  

    buttonFallback = request.GET.get('button', 'false')

    if cftsSettings.EMAIL_HOST != '' and buttonFallback == "false":
        eml = render_to_string('partials/Drop_partials/dropEmailTemplate.html', {'url': url, 'deleteDate': dropRequest.delete_on,
                            'PIN': dropRequest.request_code, 'decryptPhrase': decryptedPhrase, 'EMAIL_HOST': buttonFallback, 'EMAIL_CLASSIFICATION': cftsSettings.EMAIL_CLASSIFICATION}, request)

        email = EmailMessage(
            '[' + cftsSettings.EMAIL_CLASSIFICATION + '] CFTS File Drop',
            eml,
            "Combined File Transfer Service <" + cftsSettings.EMAIL_FROM_ADDRESS + ">",
            [str(dropRequest.target_email), ],
            reply_to=[cftsSettings.IM_ORGBOX_EMAIL, ],
        )

        email.send(fail_silently=False)
    else:
        eml = "mailto:" + str(dropRequest.target_email) + "?subject=[" + cftsSettings.EMAIL_CLASSIFICATION + "] CFTS File Drop&body=" 
        
        eml += render_to_string('partials/Drop_partials/dropEmailTemplate.html', {'url': url, 'deleteDate': dropRequest.delete_on,
                                'PIN': dropRequest.request_code, 'decryptPhrase': decryptedPhrase, 'EMAIL_HOST': buttonFallback, 'EMAIL_CLASSIFICATION': cftsSettings.EMAIL_CLASSIFICATION}, request)

    dropRequest.email_sent = True
    dropRequest.save()

    if cftsSettings.EMAIL_HOST == '' or buttonFallback == "true":
        return redirect("/drop-zone?eml="+eml)

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def processDrop(request):
    try:
        send_fail = False

        drop_folder = cftsSettings.DROPS_TEMPDIR+"\\drop_1"

        i = 2
        while True:
            if os.path.isdir(drop_folder):
                drop_folder = cftsSettings.DROPS_TEMPDIR+"\\drop_"+str(i)
                i += 1
            else:
                break

        zip = ZipFile(request.FILES.getlist("dropZip")[0], 'r')
        zip.extractall(drop_folder)

        requestPaths = set(treeScan([], drop_folder))

        request_info_re = re.compile('_request_info.txt')
        notes_re = re.compile('_notes.txt')
        for path in requestPaths:
            with open(path+"\\_request_info.txt", 'rb') as infile:
                request_info = ast.literal_eval(infile.read().decode('utf-8'))
                infile.close()

            dropRequest = Drop_Request(
                target_email=getOrCreateEmail(request, request_info['email'], cftsSettings.NETWORK),
                request_info=request_info,
                delete_on=timezone.now() + datetime.timedelta(days=5),
                request_code=''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(8)),
            )
            dropRequest.save()

            for f in os.scandir(path):
                filePath = f.path

                if request_info_re.match(filePath.split("\\")[-1]) == None and notes_re.match(filePath.split("\\")[-1]) == None:
                    with open(filePath, mode='rb') as inFile:
                        fileObj = DjangoFile(inFile, name=f.name)
                        dropFile = Drop_File(
                            file_object=fileObj,
                        )

                        dropFile.save()

                    # save the file, let Django strip illegal characters from the path, and trim the dir path from the filename

                    dropFile.file_name = str(dropFile.file_object.name).split("/")[-1]

                    dropFile.save()

                    # add the file to the request and the list of files used in the request hash
                    dropRequest.files.add(dropFile)
                    dropRequest.save()

            if cftsSettings.EMAIL_HOST != '':
                try:
                    dropEmail(request, dropRequest.request_id)
                except:
                    send_fail = True

        shutil.rmtree(drop_folder)
        if cftsSettings.EMAIL_HOST != '':
            if send_fail == True:
                messages.warning(request, "Requests Upload Successful, some emails failed to send")
            else:
                messages.success(request, "Requests Upload Successful, emails sent to users")
        else:
            messages.success(request, "Requests Upload Successful")
        fileCleanup(request)

    except Exception as e:
        logger.error(e)
        messages.error(request, "Error Creating Requests, " + str(e))
    return HttpResponse(set(requestPaths))


def dropDetails(request, id, PIN=None):
    drop = Drop_Request.objects.get(request_id=id)

    if PIN == None:
        return render(request, 'pages/dropDetails.html', {'status': "prompt"})
    elif PIN == drop.request_code:
        return render(request, 'pages/dropDetails.html', {'status': "authorized", 'drop': drop})
    else:
        return render(request, 'pages/dropDetails.html', {'status': "not authorized"})

def dropDownload(request, id, phrase=None):
    dropRequest = Drop_Request.objects.get(request_id=id)

    requestInfo = ast.literal_eval(dropRequest.request_info)

    if phrase != None:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=requestInfo['salt'], iterations=390000)
        key = kdf.derive(str.encode(phrase, 'utf-8'))

        zip_buffer = io.BytesIO()
        zipMem = ZipFile(zip_buffer, 'w')

        for file in dropRequest.files.all():
            cipher = Cipher(algorithms.AES(key), modes.CTR(requestInfo['nonce']))
            decryptor = cipher.decryptor()

            with open(file.file_object.path, 'rb') as inFile:
                decryptText = decryptor.update(inFile.read()) + decryptor.finalize()
                inFile.close()

            zipMem.writestr(file.file_name, decryptText)

        zipMem.close()
        zip_buffer.seek(0)

        dropRequest.user_retrieved = True
        dropRequest.save()

        # messages.warning(request, "If your files do not open properly, make sure you have entered in the correct Decryption Phrase (Case Senesitve)")

        return FileResponse(zip_buffer, as_attachment=True, filename='CFTS_Files.zip')
