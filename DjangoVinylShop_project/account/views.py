from django.shortcuts import render, redirect
from .forms import CreateUserForm, LoginForm

from django.contrib.sites.shortcuts import get_current_site

from .token import user_tokenizer_generate
from django.template.loader import render_to_string

from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from django.contrib.auth.models import User, auth
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required

from payment.forms import ShippingForm
from payment.models import ShippingAddress, Order, OrderItem





# Create your views here.

def register(request):

    form = CreateUserForm()

    if request.method == 'POST':

        form = CreateUserForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.is_active = False

            user.save()

            #email verification setup

            current_site = get_current_site(request)

            subject = 'Account verification email'

            message = render_to_string('account/registration/email-verification.html', {

                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': user_tokenizer_generate.make_token(user),


            })

            user.email_user(subject=subject, message=message)

            return redirect('email-verification-sent')
          
        

    context = {'form':form}
       
    return render(request, 'account/registration/register.html', context=context)




def email_verification(request, uidb64, token):

    #unique id

    unique_id = force_str(urlsafe_base64_decode(uidb64))

    user = User.objects.get(pk=unique_id)

    #Success

    if user and user_tokenizer_generate.check_token(user, token):
        user.is_active = True
        user.save()

        return redirect('email-verification-success')


    #Failed

    else:
        return redirect('email-verification-failed')


  


def email_verification_sent(request):

    return render(request, 'account/registration/email-verification-sent.html')


def email_verification_success(request):

    return render(request, 'account/registration/email-verification-success.html')


def email_verification_failed(request):

    return render(request, 'account/registration/email-verification-failed.html')


def my_login(request):

    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():

            username = request.POST.get('username')
            password = request.POST.get('password')

            user =  authenticate(request, username=username, password=password)

            if user is not None:

                auth.login(request, user)

                return redirect('dashboard')
            
    context = {'form': form}

    return render(request, 'account/my-login.html', context=context)



#logout

def user_logout(request):

    auth.logout(request)

    return redirect('store')






@login_required(login_url='my-login')
def dashboard(request):
    return render(request, 'account/dashboard.html')



# shipping view
@login_required(login_url='my-login')
def manage_shipping(request):
    try:
        # logged user with shipment information
        shipping = ShippingAddress.objects.get(user=request.user.id)
    
    except ShippingAddress.DoesNotExist:
        # logged user without shipment information
        shipping = None

    form = ShippingForm(instance=shipping)

    if request.method == 'POST':
        form = ShippingForm(request.POST, instance=shipping)

        if form.is_valid():
            # assign user foreigh key on the object
            shipping_user = form.save(commit=False)
            # adding the foreigh key to itself
            shipping_user.user = request.user
            shipping_user.save()

            return redirect('dashboard')
        
    context = {'form':form}
    return render(request, 'account/manage-shipping.html', context=context)
        
@login_required(login_url='my-login')        
def track_orders(request):
    try:
        orders = OrderItem.objects.filter(user=request.user)
        context = {'orders':orders}
        return render(request, 'account/track-orders.html', context=context)
    
    except:
        return render(request, 'account/track-orders.html', context=context)
