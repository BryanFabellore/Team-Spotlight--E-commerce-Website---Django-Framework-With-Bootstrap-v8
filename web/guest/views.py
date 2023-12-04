from django.http import HttpResponse
from django.template import loader

from . import models 
from fchub.models import Product
from fchub.models import Category

from django.shortcuts import render


def guest(request):
  template = loader.get_template('guest.html')
  return HttpResponse(template.render())

def index(request):
    if request.customer_id is not None:
        # A customer is logged in, use their customer_id and username
        customer_id = request.customer_id
        customer_username = request.customer_username
        return render(request, 'index.html', {'customer_id': customer_id, 'customer_username': customer_username})
    else:
        # Guest user, you can handle this case differently if needed
        return render(request, 'index.html', {'customer_id': None, 'customer_username': "Guest"})


def products(request):
    # Get the query parameters from the request
    fabric_type = request.GET.get('fabric_type')
    set_type = request.GET.get('set_type')
    color = request.GET.get('color')
    
    # Query the Product model based on the filters
    products = Product.objects.all()
    
    if fabric_type:
        products = products.filter(category__fabric=fabric_type)
    if set_type:
        products = products.filter(category__setType=set_type)
    if color:
        products = products.filter(color__icontains=color)  # Use 'icontains' for case-insensitive search
    
    fabric_choices = Category.FABRIC_CHOICES
    set_type_choices = Category.SET_TYPE_CHOICES
    
    # Render the template with the filtered products and choices
    return render(request, 'products.html', {'products': products, 'FABRIC_CHOICES': fabric_choices, 'SET_TYPE_CHOICES': set_type_choices})
