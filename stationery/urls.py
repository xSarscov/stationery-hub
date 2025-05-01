from django.urls import path
from .views import *

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('shop/',ShopView.as_view(),name='shop'),
    path('shopProduct/',ShopProductView.as_view(),name='shopProduct'),
    path('contact/',ContactView.as_view(),name='contact'),
    path('blog/',CREATEBlogView.as_view(),name='blog'),
    path('blog1/',Blogview.as_view(),name='blog1')
]