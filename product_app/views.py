from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth import logout, get_user_model # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.core.mail import send_mail # type: ignore
from django.conf import settings # type: ignore
from django.contrib import messages # type: ignore
from django.http import JsonResponse, HttpResponse # type: ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore

import random
import stripe # type: ignore

from .forms import CustomUserCreationForm, ProductForm
from .models import CustomUser, Product, Order

stripe.api_key = settings.STRIPE_SECRET_KEY


# ------------------------ AUTH VIEWS ------------------------

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.is_verified = False
            user.is_active = False
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
    email = request.session.get('user_email')
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        user = CustomUser.objects.filter(email=email).first()
        if user and user.otp == entered_otp:
            user.is_verified = True
            user.is_active = True
            user.otp = ''
            user.save()
            messages.success(request, "Account verified. Please log in.")
            return redirect('login')
        messages.error(request, "Invalid OTP. Try again.")
    return render(request, 'product_app/verify_otp.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.save()
            send_mail(
                'Reset Password OTP',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            request.session['reset_email'] = email
            return redirect('verify_otp_reset')
        except CustomUser.DoesNotExist:
            return render(request, 'product_app/forgot_password.html', {'error': 'Email not found'})
    return render(request, 'product_app/forgot_password.html')


def verify_otp_reset(request):
    email = request.session.get('reset_email')
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        try:
            user = CustomUser.objects.get(email=email)
            if user.otp == entered_otp:
                user.otp = ''
                user.save()
                return redirect('reset_password')
            else:
                return render(request, 'product_app/verify_otp.html', {'error': 'Invalid OTP'})
        except CustomUser.DoesNotExist:
            return redirect('forgot_password')
    return render(request, 'product_app/verify_otp.html')


def reset_password(request):
    email = request.session.get('reset_email')
    if request.method == 'POST':
        password = request.POST.get('password')
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(password)
            user.otp = None
            user.save()
            return redirect('login')
        except CustomUser.DoesNotExist:
            return redirect('forgot_password')
    return render(request, 'product_app/reset_password.html')


@login_required
def custom_logout(request):
    logout(request)
    return redirect('/')


# ------------------------ PRODUCT VIEWS ------------------------

def home(request):
    products = Product.objects.all()
    purchased_items = Order.objects.filter(user=request.user) if request.user.is_authenticated else Order.objects.none()
    return render(request, 'product_app/home.html', {
        'products': products,
        'purchased_items': purchased_items
    })


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            return redirect('home')
    else:
        form = ProductForm()
    return render(request, 'product_app/product_form.html', {'form': form})


@login_required
def update_product(request, id):
    product = get_object_or_404(Product, id=id)
    if product.user != request.user:
        return redirect('home')
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('home')
    return render(request, 'product_app/product_form.html', {'form': form})


@login_required
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    if product.user != request.user:
        return redirect('home')
    if request.method == 'POST':
        product.delete()
        return redirect('home')
    return render(request, 'product_app/confirm_delete.html', {'product': product})


# ------------------------ PAYMENT VIEWS ------------------------

@login_required
def buy_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.user == request.user:
        messages.warning(request, "You cannot buy your own product.")
        return redirect("home")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': product.name},
                    'unit_amount': int(product.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
            customer_email=request.user.email,
        )
        request.session['product_id'] = product.id
        request.session['checkout_session_id'] = checkout_session.id
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect("home")


@login_required
def payment_success(request):
    product_id = request.session.get('product_id')
    session_id = request.session.get('checkout_session_id')

    if not product_id or not session_id:
        messages.error(request, "Invalid session.")
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)

    if not Order.objects.filter(user=request.user, stripe_checkout_session_id=session_id).exists():
        Order.objects.create(
            user=request.user,
            product=product,
            stripe_checkout_session_id=session_id
        )

    messages.success(request, "Payment successful. Order placed!")
    return redirect('home')


def payment_cancel(request):
    return render(request, 'product_app/cancel.html')


# ------------------------ ERROR HANDLING ------------------------

def custom_404(request, exception):
    return render(request, 'product_app/404.html', status=404)

def create_checkout_session(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Yeh bas dummy response hai, actual Stripe logic baad me add kar sakte ho
    return JsonResponse({'message': f'Checkout session created for {product.name}'})