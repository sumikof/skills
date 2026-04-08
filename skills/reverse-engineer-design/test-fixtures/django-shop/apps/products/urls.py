from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list"),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
    path("category/<slug:slug>/", views.CategoryProductListView.as_view(), name="by-category"),
]

api_urlpatterns = [
    path("", views.ProductListAPIView.as_view(), name="api-list"),
    path("<int:pk>/", views.ProductDetailAPIView.as_view(), name="api-detail"),
    path("categories/", views.CategoryListAPIView.as_view(), name="api-categories"),
    path("categories/<int:pk>/", views.CategoryDetailAPIView.as_view(), name="api-category-detail"),
]
