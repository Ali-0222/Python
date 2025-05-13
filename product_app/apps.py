from django.apps import AppConfig # type: ignore


class ProductAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'product_app'
