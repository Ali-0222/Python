# product_app/forms.py

from django import forms # type: ignore
from .models import CustomUser, Product
from django.contrib.auth.forms import UserCreationForm # type: ignore

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['email']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price']
