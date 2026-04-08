from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """拡張ユーザーモデル"""
    phone = models.CharField(max_length=15, blank=True, verbose_name="電話番号")
    address = models.TextField(blank=True, verbose_name="住所")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="郵便番号")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"
