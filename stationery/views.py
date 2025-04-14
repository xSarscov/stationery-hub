from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class HomeView(TemplateView):
    template_name = 'stationery/index.html'

class ShopView(TemplateView):
    template_name = 'stationery/shop.html'

class ShopProductView(TemplateView):
    template_name= 'stationery/shop-single.html'

class ContactView(TemplateView):
    template_name='stationery/contact.html'

class BlogView(TemplateView):
    template_name='stationery/blog-single.html'


