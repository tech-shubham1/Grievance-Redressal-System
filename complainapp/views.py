from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import *
from .models import *
from django.utils import timezone
from django.db.models import Q, F, Count
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import datetime
from .isoffensive import is_offensive
import threading

TODAY_DATE = None
lock = threading.Lock()
def check_escalation():
    global TODAY_DATE
    # Use a lock to ensure that only one thread can access and modify TODAY_DATE at a time
    with lock:
        if TODAY_DATE is not None and TODAY_DATE == timezone.datetime.now().date():
            return
        TODAY_DATE = timezone.datetime.now().date()

    current_date = timezone.datetime.now()
    # Get all active complaints that are due for escalation and have a non-null parent designation
    complains = Complain.objects.filter(
        completed=False,
        response_date__lte=current_date,
        registered_to__parent__isnull=False
    )

    for complain in complains:
        parent_designation = complain.registered_to.parent
        complain.registered_to = parent_designation
        str_now = datetime.now().strftime('%a, %d %b %Y at %H:%M')
        complain.description = (
            f'<p><strong><span style="color: rgb(53, 152, 219);">'
            f'On {str_now}, complain escalated due to response date timeout by {parent_designation.name}'
            f'</span>&nbsp;</strong></p>'
            f'<blockquote>{complain.description}'
            f'</blockquote>'
        )
        complain.response_date = timezone.now().date() + timezone.timedelta(days=3)
        complain.save()

def check_escalation_wrapper(func):
    def wrapper(*args, **kwargs):
        check_escalation()
        return func(*args, **kwargs)
    return wrapper

  
def check_designation(user):
    return Profile.objects.get(user=user).designation_holder.exists()

@check_escalation_wrapper
def index(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        answered_complains = Complain.objects.filter(registered_by=profile, completed=True)
        unanswered_complains = Complain.objects.filter(registered_by=profile, completed=False)
        reopencomplainform = ReopenComplainForm()
        escalatecomplainform = EscalateComplainForm()
        return render(request, 'complainapp/index.html', {'answered_complains': answered_complains, 
                                                          'unanswered_complains': unanswered_complains, 
                                                          'reopencomplainform': reopencomplainform, 
                                                          'escalatecomplainform': escalatecomplainform})
    else:
        signupform = SignupForm()
        loginform = LoginForm()
        return render(request, "complainapp/authentication.html", {'signupform': signupform, 'loginform': loginform})


def handleLogin(request):
    if request.method == "POST":
        loginform = LoginForm(request.POST)
        if (loginform.is_valid()):
            email = loginform.cleaned_data['email']
            if (email.endswith('@iiitl.ac.in') == False):
                messages.error(request, "Please use your IIITL email")
                return redirect('/')
            password = loginform.cleaned_data['password']
            user = authenticate(username=email, password=password)
            if (user is not None):
                login(request, user)
                messages.success(
                    request, f"Welcome {user.first_name}, you have logged in successfully.")
                return redirect('/')
            else:
                messages.error(
                    request, "Invalid Credentials, Please try again")
                return redirect('/')
    messages.error(
        request, "Some Error Occured, Please try again or contact us")
    return redirect('/')


def handleSignup(request):
    if request.method == "POST":
        signupform = SignupForm(request.POST)
        if signupform.is_valid():
            first_name = signupform.cleaned_data['first_name']
            last_name = signupform.cleaned_data['last_name']
            email = signupform.cleaned_data['email']
            if (email.endswith('@iiitl.ac.in') == False):
                messages.error(
                    request, "Please register with your IIITL email")
                return redirect('index')
            pass1 = signupform.cleaned_data['pass1']
            pass2 = signupform.cleaned_data['pass2']
            if (pass1 != pass2):
                messages.error(request, "Passwords do not match")
                return redirect('index')
            # check user already exists
            if (User.objects.filter(username=email).exists()):
                messages.error(request, "User already exists")
                return redirect('index')
            myuser = User.objects.create_user(email, email, pass1)
            myuser.first_name = first_name
            myuser.last_name = last_name
            myuser.save()
            myprofile = Profile(user=myuser, data={})
            myprofile.save()
            messages.success(
                request, "Your account has been successfully created")
            return redirect('index')
    messages.error(
        request, "Some Error Occured, Please try again or contact us")
    return redirect('index')

@login_required(login_url='/')
def handleLogout(request):
    logout(request)
    messages.success(request, "Successfully Logged Out")
    return redirect('/')


@login_required(login_url='/')
@check_escalation_wrapper
def respondComplain(request):
    if request.method == "POST":
        complain_id = request.POST.get('complain_id')
        complain = Complain.objects.get(id=complain_id)
        response = request.POST.get('response')
        if is_offensive(response): 
            messages.warning(request, "Response contains offensive words !!!")
            return redirect('respondComplain')
        str_now = datetime.now().strftime('%a, %d %b %Y at %H:%M')
        response_by = complain.registered_to.name
        response_by_email = complain.registered_to.designation_holder.user.email
        complain.description = (
            f'<p><strong><span style="color: rgb(53, 152, 219);">'
            f'On {str_now}, response by {response_by} &lt;{response_by_email}&gt;:'
            f'</span>&nbsp;</strong></p>'
            f'{response}'
            f'<blockquote>{complain.description}'
            f'</blockquote>'
        )
        complain.response_date = now()
        complain.completed = True
        complain.save()
        messages.success(request, "Complain Responded Successfully")
        return redirect('respondComplain')

    if not check_designation(request.user):
        messages.error(request, "You do not hold any designation")
        return redirect('/')
    myprofile = Profile.objects.get(user=request.user)
    designation_set = myprofile.designation_holder.all()
    complains_list = dict()
    for designation in designation_set:
        complains_list[designation] = Complain.objects.filter(
            registered_to=designation, completed=False)
    return render(request, "complainapp/respondcomplain.html", {'complains_list': complains_list, 'designation_holder': True})

@login_required(login_url='/')
@check_escalation_wrapper
def allcomplain(request):
    allcomplain = Complain.objects.filter(completed=False).annotate(like_count=Count('likes')).order_by('-like_count')
    return render(request,'complainapp/allcomplains.html',{'allcomplain':allcomplain})

@login_required(login_url='/')
def postlike(request):
    user = request.user
    if(request.method == 'POST'):
        post_id = request.POST.get('cid')
        post_obj = Complain.objects.get(id=post_id)

        if(user in post_obj.likes.all()):
            post_obj.likes.remove(user)
        else:
            post_obj.likes.add(user)
        
        like, created = Like.objects.get_or_create(user=user, post_id = post_id)

        if not created:
            if(like.value == 'like'):
                like.value = 'unlike'
            else:
                like.value = 'like'
        like.save()

    return redirect('allcomplain')

@login_required(login_url='/')
def createComplain(request):
    all_designations = Designation.objects.all()
    if request.method == 'POST':
        form = ComplainForm(request.POST)
        if form.is_valid():
            complain = form.save(commit=False)
            str_now = datetime.now().strftime('%a, %d %b %Y at %H:%M')
            complain.registered_by = Profile.objects.get(user=request.user)
            complain.registered_date = now()
            complain.completed = False
            if (is_offensive(complain.description)): 
                messages.warning(request, "Response contains offensive words !!!")
                return redirect('createComplain')
            complain.description = (
                f'<p><strong><span style="color: rgb(53, 152, 219);">'
                f'On {str_now}, complain registered by {complain.registered_by.user.get_full_name()} &lt;{complain.registered_by.user.username}&gt;:'
                f'</span>&nbsp;</strong></p>'
                f'{complain.description}'
            )
            complain.save()
            messages.success(request, "Complain Registered Successfully")
        else:
            for error in form.errors: messages.error(request, form.errors[error])
        return redirect('createComplain')
    else:
        complainform = ComplainForm()
        return render(request, "complainapp/createcomplain.html", {'complainform': complainform, 'all_designations': all_designations})

@login_required(login_url='/')
def reopenComplain(request):
    if request.method == 'POST':
        complain_id = request.POST.get('complain_id')
        complain = Complain.objects.get(id=complain_id)
        form = ReopenComplainForm(request.POST)
        if form.is_valid():
            complain.completed = False
            complain.response_date = form.cleaned_data['response_date']
            response = form.cleaned_data['description']
            if is_offensive(response): 
                messages.warning(request, "Response contains offensive words !!!")
                return redirect('index')
            str_now = datetime.now().strftime('%a, %d %b %Y at %H:%M')
            complain.description = (
                f'<p><strong><span style="color: rgb(53, 152, 219);">'
                f'On {str_now}, complain reinitiated by {complain.registered_by.user.get_full_name()} &lt;{complain.registered_by.user.username}&gt;:'
                f'</span>&nbsp;</strong></p>'
                f'{response}'
                f'<blockquote>{complain.description}'
                f'</blockquote>'
            )
            complain.save()
            messages.success(request, "Complain Reopened Successfully")
            return redirect('index')
        else:
            for error in form.errors: messages.error(request, form.errors[error])
    else:
        form = ReopenComplainForm()

    return redirect('index')

@login_required(login_url='/')
def escalateComplain(request):  #needed some work here
    if request.method == 'POST':
        complain_id = request.POST.get('complain_id')
        response = request.POST.get('description')
        if is_offensive(response):
            messages.warning(request, "Response contains offensive words !!!")
            return redirect('index')
        complain = Complain.objects.get(id=complain_id)
        complain.completed = False
        str_now = datetime.now().strftime('%a, %d %b %Y at %H:%M')
        registered_by_user = complain.registered_by.user
        complain.description = (
            f'<p><strong><span style="color: rgb(53, 152, 219);">'
            f'On {str_now}, complain escalated manually by {registered_by_user.get_full_name()} &lt;{registered_by_user.username}&gt; due to:'
            f'</span>&nbsp;</strong></p>'
            f'{response}'
            f'<blockquote>{complain.description}'
            f'</blockquote>'
        )
        if complain.registered_to.parent is None: 
            messages.error(request, "Complain is already escalated to the highest authority")
            return redirect('index')
        complain.registered_to = complain.registered_to.parent
        complain.save()
        messages.success(request, "Complain Escalated Successfully")
    else:
        messages.error(request, "Some Error Occured, Please try again or contact us")
    return redirect('index')