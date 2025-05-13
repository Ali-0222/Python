from django.urls import path # type: ignore
from product_app import views
from django.contrib.auth.views import LoginView, LogoutView # type: ignore

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('login/', LoginView.as_view(template_name='product_app/login.html'), name='login'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.custom_logout, name='logout'),
    path('add/', views.add_product, name='add_product'),
    path('update/<int:id>/', views.update_product, name='update_product'),
    path('delete/<int:id>/', views.delete_product, name='delete_product'),
    path('verify-otp/', views.verify_otp_register, name='verify_otp'),
    path('reset-verify-otp/', views.verify_otp_reset, name='verify_otp_reset'),

]
