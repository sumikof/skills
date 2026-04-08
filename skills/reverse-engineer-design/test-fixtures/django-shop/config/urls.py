from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("products/", include("apps.products.urls")),
    path("orders/", include("apps.orders.urls")),
    path("api/v1/", include("apps.products.urls", namespace="api_v1")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
