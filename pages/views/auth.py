import hashlib
from os import name
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect

from pages.forms import NewUserForm, userInfoForm, userLogInForm, userPasswordChangeForm
from django.contrib.auth import login, authenticate
from django.contrib import messages

from django.contrib.auth.models import User as authUser
from pages.models import Network, User, Email
from pages.views.apis import setConsentCookie
from cfts.settings import NETWORK

def getCert(request):
    buggedPKIs = ['f7d359ebb99a6a8aac39b297745b741b'] #[ acutally bugged hash, my hash for testing]

    try:
        cert = request.META['CERT_SUBJECT']

        # empty cert, IIS is set to ignore certs
        if cert =="":
            return {'status': "empty"}
        
        # got a cert!
        else:
            userHash = hashlib.md5()
            userHash.update(cert.encode())
            userHash = userHash.hexdigest()
            
            if userHash in buggedPKIs:
                return {'status': "buggedPKI", 'cert': cert, 'userHash': userHash}

            # and their cert info isn't bugged!
            else:
                return {'status': "validPKI", 'cert': cert, 'userHash': userHash}

    # django dev server doesn't grab certs
    except KeyError:
        return {'status': "empty"}
        # below lines are for testing PKI with django
        #return {'status': "buggedPKI", 'cert': "test.tester2.12345", 'userHash': "f7d359ebb99a6a8aac39b297745b741b"}
        #return {'status': "validPKI", 'cert': "", 'userHash': "1234"}

def getOrCreateSourceEmail(request, email):
    emailNet = Network.objects.get(name=NETWORK)

    try:
        userEmail = Email.objects.get(address=email)
        if userEmail.network == None:
            userEmail.network = emailNet
            userEmail.save()

    except Email.DoesNotExist:
        userEmail = Email(address=email, network=emailNet)
        userEmail.save()
    
    return userEmail


def getOrCreateUser(request, certInfo):
    try:
        if certInfo['status'] == "validPKI":
            userHash = certInfo['userHash']

            user = User.objects.get(user_identifier=userHash)

            if user.auth_user == None:
                if request.user.is_authenticated:
                    user.auth_user = request.user
                    user.save()
                else:
                    return None
        else:
            if request.user.is_authenticated:
                user = User.objects.get(auth_user=request.user)
            else:
                return None
        
    except User.DoesNotExist:
        print("No user found with ID")
        if request.user.is_authenticated:
            userEmail = getOrCreateSourceEmail(request, request.user.email)
            user = User(
                auth_user = request.user,
                name_first=request.user.first_name,
                name_last=request.user.last_name,
                source_email = userEmail
            )

            if certInfo['status'] == "validPKI":
                user.user_identifier=certInfo['userHash']

            user.save()
        else:
            return None

    except KeyError:
        try:
            #print("I hope you are runing through Django server, or else I screwd up big.")
            user = User.objects.get(auth_user=request.user)

        except User.DoesNotExist:
            print("No user found with ID")
            if request.user.is_authenticated:
                userEmail = getOrCreateSourceEmail(request, request.user.email)
                user = User(
                    auth_user = request.user,
                    name_first=request.user.first_name,
                    name_last=request.user.last_name,
                    source_email = userEmail
                )
                user.save()

            else:
                return None

    return user

def userLogin(request):
    if request.method == "POST":
        form = userLogInForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                #messages.success(request, "Login successful!")
                login(request, user)

                nextUrl = request.GET.get('next', None)
                if nextUrl == None:
                    return redirect("/frontend")
                else:
                    return redirect(nextUrl)
            else:
                return render(request, template_name="authForms/userLogin.html", context={"login_form":form,})
            
        else:
            return render(request, template_name="authForms/userLogin.html", context={"login_form":form,})

    form = userLogInForm()
    return render(request, template_name="authForms/userLogin.html", context={"login_form":form})

@login_required
def changeUserPassword(request):
    if request.method == "POST":
        form = userPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            login(request, request.user)
            setConsentCookie(request)

            return redirect("/frontend")
            
        else:
            return render(request, template_name="authForms/userPassChange.html", context={"pass_change_form":form,})

    form = userPasswordChangeForm(request.user)
    return render(request, template_name="authForms/userPassChange.html", context={"pass_change_form":form})

def register(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            certInfo = getCert(request)
            cftsUser = getOrCreateUser(request, certInfo)
            cftsUser.auth_user = authUser.objects.get(id=request.user.id)
            cftsUser.phone = request.POST.get('phone')
            cftsUser.save()
            #messages.success(request, "Account creation successful!")
            setConsentCookie(request)

            return redirect("/user-info")
        else:
            return render(request, template_name="authForms/register.html", context={"register_form":form,})

    form = NewUserForm()
    return render(request, template_name="authForms/register.html", context={"register_form":form})

@login_required
def editUserInfo(request):
    nets = Network.objects.filter(visible=True)
    certInfo = getCert(request)
    cftsUser = getOrCreateUser(request, certInfo)

    if request.method == "POST":
        form = userInfoForm(request.POST, instance=cftsUser, networks=nets)
        if form.is_valid():
            # update source email address object
            userEmail = Email.objects.get(email_id=cftsUser.source_email.email_id)
            userEmail.address=request.POST.get('source_email')
            userEmail.save()

            # update auth user account info
            request.user.first_name = request.POST.get('name_first')
            request.user.last_name = request.POST.get('name_last')
            request.user.email = request.POST.get('source_email')
            request.user.save()

            # update cfts user object info
            cftsUser.name_first = request.POST.get('name_first')
            cftsUser.name_last = request.POST.get('name_last')
            cftsUser.source_email = userEmail
            cftsUser.phone = request.POST.get('phone')
            cftsUser.update_info = False
            
            # create or update destination emails
            for net in nets:
                formEmail = request.POST.get(str(net.name)+' Email')

                if formEmail != "":
                    try:
                        destinationEmail = cftsUser.destination_emails.get(network__name=net.name)
                        if formEmail != destinationEmail:
                            destinationEmail.address = formEmail
                            destinationEmail.save()
                    # user does not have a destination Email with this address, search all Email objects 
                    except Email.DoesNotExist:
                        try:
                            destinationEmail = Email.objects.get(address=formEmail)
                            if destinationEmail.network == None:
                                destinationEmail.network = Network.objects.get(name=net.name)
                                destinationEmail.save()

                            cftsUser.destination_emails.add(destinationEmail)

                        except Email.DoesNotExist:
                            destinationEmail = Email(address=formEmail, network=Network.objects.get(name=net.name))
                            destinationEmail.save()
                            
                            cftsUser.destination_emails.add(destinationEmail)

            cftsUser.save()
            
            return redirect("/frontend")
        else:
            return render(request, 'authForms/editUserInfo.html', context={"userInfoForm": form})

    form = userInfoForm(instance=cftsUser, networks=nets)
    return render(request, 'authForms/editUserInfo.html', context={"userInfoForm": form})