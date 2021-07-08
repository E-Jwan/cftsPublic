# ====================================================================
# core
from email import generator
import random
import datetime
# from io import BytesIO, StringIO
from zipfile import ZipFile, Path
from django.conf import settings

# decorators
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

# responses
from django.shortcuts import render
from django.http import JsonResponse, FileResponse, response  # , HttpResponse,

# model/database stuff
from pages.models import *
from django.db.models import Max, Count, Q, Sum

# email creation
from email.generator import Generator
from email.mime.text import MIMEText
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import mimetypes
import warnings
from pathlib import Path
# ====================================================================


@login_required
@ensure_csrf_cookie
def queue(request):
    xfer_queues = []
    ds_networks = Network.objects.all()
    empty = random.choice([
        'These pipes are clean.',
        'LZ is clear.',
        'Nothing here. Why not work on metadata?',
        'Queue is empty -- just like my wallet.',
        "There's nothing here? Huh. That's gotta be an error ... ",
        "Xander was here."
    ])

    ########################
    # FOR EACH NETWORK ... #
    ########################
    for net in ds_networks:
        # get information about the last pull that was done on each network
        last_pull = Pull.objects.values(
            'pull_number',
            'date_pulled',
            'user_pulled__username'
        ).filter(network__name=net.name).order_by('-date_pulled')[:1]

        # get all the xfer requests (pending and pulled) submitted for this network
        ds_requests = Request.objects.filter(
            network__name=net.name,
            is_submitted=True,
            pull__date_complete__isnull=True
            # , files__in=File.objects.filter( rejection_reason__isnull=True )
        ).order_by('-date_created')

        # count how many total files are in all the pending requests (excluding ones that have already been pulled)
        file_count = ds_requests.annotate(
            files_in_request=Count('files__file_id', filter=Q(
                pull__date_pulled__isnull=True))
        ).aggregate(
            files_in_dataset=Sum('files_in_request')
        )

        # smoosh all the info together into one big, beautiful data object ...
        queue = {
            'name': net.name,
            'order_by': net.sort_order,
            'file_count': file_count,
            'count': ds_requests.count(),
            'pending': ds_requests.aggregate(count=Count('request_id', filter=Q(pull__date_pulled__isnull=True))),
            'q': ds_requests,
            'centcom': ds_requests.aggregate(count=Count('request_id', filter=Q(pull__date_pulled__isnull=True, centcom_pull=True))),
            'last_pull': last_pull
        }
        # ... and add it to the list
        xfer_queues.append(queue)

    # sort the list of network queues into network order
    xfer_queues = sorted(
        xfer_queues, key=lambda k: k['order_by'], reverse=False)

    # get list of Rejections for the "Reject Files" button
    ds_rejections = Rejection.objects.all()
    rejections = []
    for row in ds_rejections:
        rejections.append({
            'rejection_id': row.rejection_id,
            'name': row.name,
            'subject': row.subject,
            'text': row.text
        })

    # create the request context
    rc = {'queues': xfer_queues, 'empty': empty, 'rejections': rejections}

    # roll that beautiful bean footage
    return render(request, 'pages/queue.html', {'rc': rc})


@login_required
def transferRequest( request, id ):
    rqst = Request.objects.get( request_id = id )
    rc = { 
        'request_id': rqst.request_id,
        'date_created': rqst.date_created,
        'user': User.objects.get( user_id = rqst.user.user_id ),
        'phone': User.objects.get(user_id=rqst.user.user_id).phone,
        'network': Network.objects.get( network_id = rqst.network.network_id ),
        'files': rqst.files.all(),
        'target_email': rqst.target_email.all(),
        'is_submitted': rqst.is_submitted,
        'is_centcom': User.objects.get(user_id=rqst.user.user_id).is_centcom
    }
    return render(request, 'pages/transfer-request.html', {'rc': rc})


@login_required
def createZip(request, network_name, isCentcom):
    # create pull
    maxPull = Pull.objects.aggregate(Max('pull_number'))
    pull_number = 1 if maxPull['pull_number__max'] == None else maxPull['pull_number__max'] + 1

    if isCentcom == "True":
        new_pull = Pull(
            pull_number=pull_number,
            network=Network.objects.get(name=network_name),
            date_pulled=datetime.datetime.now(),
            user_pulled=request.user,
            centcom_pull=True
        )
    else:
        new_pull = Pull(
            pull_number=pull_number,
            network=Network.objects.get(name=network_name),
            date_pulled=datetime.datetime.now(),
            user_pulled=request.user,
        )
    new_pull.save()

    # create/overwrite zip file
    zipPath = os.path.join(
        settings.STATICFILES_DIRS[0], "files\\") + network_name + "_" + str(pull_number) + ".zip"
    zip = ZipFile(zipPath, "w")

    # select Requests based on network and status
    if(isCentcom == "True"):
        qs = Request.objects.filter(
            network__name=network_name, pull=None, is_centcom=True)
        for rqst in qs:
          rqst.centcom_pull = True

    elif(isCentcom == "False"):
        qs = Request.objects.filter(
            network__name=network_name, pull=None)
    # for each xfer request ...
    for rqst in qs:
        zip_folder = str(rqst.user)
        theseFiles = rqst.files.filter(rejection_reason=None)
        # add their files to the zip in the folder of their name
        for f in theseFiles:
            zip_path = os.path.join(zip_folder, str(f))
            zip.write(f.file_object.path, zip_path)

        # create and add the target email file
        email_file_name = '_email.txt'
        email_file_path = zip_folder + "/" + email_file_name

        if email_file_path in zip.namelist():
            i = 1
            print("txt file exists")
            while True:
                email_file_name = "_email"+str(i)+".txt"
                email_file_path = zip_folder + "/" + email_file_name

                print("Trying " + email_file_name)
                if email_file_path in zip.namelist():
                    i = i + 1
                else:
                    break
        
        fp = open(email_file_name, "w")
        emailString = ""

        for this_email in rqst.target_email.all():
            emailString = emailString + this_email.address + ';\n'
        
        fp.write(emailString)
        fp.close()

        zip.write(email_file_name, os.path.join(zip_folder, email_file_name))
        os.remove(email_file_name)
        

        msg = MIMEMultipart()

        msg['To'] = emailString
        msg['Subject'] = 'CFTS File Transfer'

        msg.attach(MIMEText('Attatched files transfered across domains from CFTS.'))

        for f in theseFiles:
            fileMime = mimetypes.guess_type(f.file_object.path)
            
            file = open(f.file_object.path.encode('utf-8'),'rb')
            attachment = MIMEBase(fileMime[0],fileMime[1])
            attachment.set_payload(file.read())
            file.close()
            encode_base64(attachment)
            attachment.add_header('Content-Disposition','attachment',filename=f.file_object.path.split("\\")[-1])
            msg.attach(attachment)

        msg_file_name = '_email.eml'
        msgPath =zip_folder+"/"+msg_file_name

        if msgPath in zip.namelist():
            i = 1
            print("eml file exists")
            while True:
                msg_file_name = "_email"+str(i)+".eml"
                msgPath =zip_folder+"/"+msg_file_name
                print("Trying " + msg_file_name)
                if msgPath in zip.namelist():
                    i = i + 1
                else:
                    break        


        with open(msg_file_name.encode("utf-8"), 'w') as eml:
            gen = Generator(eml)
            gen.flatten(msg)


        zip.write(msg_file_name, os.path.join(zip_folder, msg_file_name))
        os.remove(msg_file_name)

        # update the record
        rqst.pull_id = new_pull.pull_id
        rqst.save()

    zip.close()

    # see if we can't provide something more useful to the analysts - maybe the new pull number?
    return JsonResponse({'pullNumber': new_pull.pull_number, 'datePulled': new_pull.date_pulled.strftime("%d%b %H%M").upper(), 'userPulled': str(new_pull.user_pulled)})



@login_required
def getFile(request, fileID, fileName):
  response = FileResponse(
      open(os.path.join("uploads", fileID, fileName), 'rb'))
  return response
