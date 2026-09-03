from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="home"),
    path(
        "products/create/",
        views.ProductCreateView.as_view(),
        name="product_create",
    ),
    path(
        "products/<int:pk>/",
        views.ProductDetailView.as_view(),
        name="product_detail",
    ),
    path(
        "categories/<int:pk>/products/",
        views.CategoryProductsView.as_view(),
        name="category_products",
    ),
    path(
        "products/<int:pk>/update/",
        views.ProductUpdateView.as_view(),
        name="product_update",
    ),
    path(
        "products/<int:pk>/delete/",
        views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
    path(
        "contacts/",
        views.ContactsView.as_view(),
        name="contacts",
    ),
]
