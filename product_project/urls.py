from django.contrib import admin # type: ignore
from django.urls import path, include # type: ignore

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('product_app.urls')),
]
handler404 = 'product_app.views.custom_404'
