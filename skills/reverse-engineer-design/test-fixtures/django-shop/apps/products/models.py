from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="カテゴリ名")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "カテゴリ"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="商品名")
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="商品説明")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="価格")
    stock = models.PositiveIntegerField(default=0, verbose_name="在庫数")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "商品"

    def __str__(self):
        return self.name
