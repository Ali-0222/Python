from django.contrib import admin  # type: ignore
from .models import CustomUser, Product
from django.contrib.auth.admin import UserAdmin  # type: ignore

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
    )

# Read-Only Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price')  # optional: display fields
    readonly_fields = [field.name for field in Product._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Product, ProductAdmin)
