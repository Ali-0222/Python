# product_app/views.py

from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from .forms import CustomUserCreationForm, ProductForm
from .models import Product
from django.contrib.auth.decorators import login_required # type: ignore
from django.contrib.auth import logout # type: ignore
import random
from django.core.mail import send_mail # type: ignore
from django.conf import settings # type: ignore
from .models import CustomUser
from django.contrib import messages # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from django.shortcuts import render # type: ignore


def home(request):
    products = Product.objects.all()
    return render(request, 'product_app/home.html', {'products': products})


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user  # 👈 Set the user
            product.save()
            return redirect('home')
    else:
        form = ProductForm()
    return render(request, 'product_app/product_form.html', {'form': form})



@login_required
def update_product(request, id):
    product = get_object_or_404(Product, id=id)

    if product.user != request.user:
        return redirect('home')  # 👈 Prevent other users from editing

    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('home')
    return render(request, 'product_app/product_form.html', {'form': form})


@login_required
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)

    if product.user != request.user:
        return redirect('home')  # 👈 Prevent other users from deleting

    if request.method == 'POST':
        product.delete()
        return redirect('home')
    return render(request, 'product_app/confirm_delete.html', {'product': product})


@login_required
def custom_logout(request):
    logout(request)
    return redirect('/')

def generate_otp():
    return str(random.randint(100000, 999999))

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            otp = generate_otp()
            user.otp = otp
            user.is_verified = False
            user.is_active = False  # Make sure the user is inactive until OTP is verified
            user.save()

            send_mail(
                'Your OTP Code',
                f'Your OTP code is: {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            request.session['user_email'] = user.email
            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'product_app/register.html', {'form': form})

def verify_otp_register(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        email = request.session.get('user_email')
        user = CustomUser.objects.filter(email=email).first()

        if user and user.otp == entered_otp:
            user.is_verified = True
            user.is_active = True  # ✅ Activate user after successful OTP verification
            user.otp = ''
            user.save()
            messages.success(request, "Account verified. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Try again.")
    
    return render(request, 'product_app/verify_otp.html')



User = get_user_model()

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.save()
            send_mail(
                'Your OTP Code',
                f'Your OTP for resetting password is {otp}',
                    settings.EMAIL_HOST_USER,  # 👈 Add this (from_email)
                    [user.email],              # 👈 Add this (recipient_list)
                fail_silently=False,
            )
            request.session['reset_email'] = email
            return redirect('verify_otp_reset')
        except User.DoesNotExist:
            return render(request, 'product_app/forgot_password.html', {'error': 'Email not found'})
    return render(request, 'product_app/forgot_password.html')

def verify_otp_reset(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')
        entered_otp = request.POST.get('otp')

        try:
            user = User.objects.get(email=email)
            if user.otp == entered_otp:
                user.is_verified = True
                user.otp = ''  # Clear the OTP after successful verification
                user.save()
                return redirect('reset_password')  # Proceed to reset password
            else:
                return render(request, 'product_app/verify_otp.html', {'error': 'Invalid OTP'})
        except User.DoesNotExist:
            return redirect('forgot_password')

    return render(request, 'product_app/verify_otp.html')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        email = request.session.get('reset_email')
        user = User.objects.get(email=email)
        user.set_password(password)
        user.otp = None
        user.save()
        return redirect('login')
    return render(request, 'product_app/reset_password.html')


def custom_404(request, exception):
    return render(request, 'product_app/404.html', status=404)
