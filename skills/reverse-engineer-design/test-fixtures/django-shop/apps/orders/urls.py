from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/add/", views.CartAddView.as_view(), name="cart-add"),
    path("cart/remove/<int:item_id>/", views.CartRemoveView.as_view(), name="cart-remove"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("webhook/stripe/", views.StripeWebhookView.as_view(), name="stripe-webhook"),
]
