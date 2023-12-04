from collections import defaultdict
from email.message import EmailMessage
from django.core.mail import send_mail
import calendar
from decimal import Decimal
from io import TextIOWrapper
import io
from itertools import product
import json
from django.db.models import F, Sum
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.cache import cache
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.views import View
import joblib
from matplotlib import pyplot as plt
from sklearn.calibration import LabelEncoder
from sklearn.compose import TransformedTargetRegressor
from sklearn.discriminant_analysis import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from customer.models import Address, Customer, Order, Product, OrderItem
from web.settings import BASE_DIR
from .models import CleanTrainingSets, CsvData, CurtainIngredients, FabricMaterial, Inventory, Material, FleekyAdmin, Category, SalesForCategory, SalesForColor, SalesForFabric, SalesForLocation, SalesForWebData, SuccessfulOrder, Tracker, User, TrainingSets
from .forms import  CategoryForm, CsvUploadForm, CurtainIngredientsForm,FabricMaterialForm, FleekyAdminForm, MaterialForm, ProductForm, TrackerForm
from django.contrib.auth.forms import UserCreationForm
from .models import Csv  # Make sure you have this import
import csv
from .models import CsvData
from django.contrib import messages
import os
from django.db.models import Q
from django.core.exceptions import ValidationError
from datetime import date, datetime
from xhtml2pdf import pisa
from django.template.loader import get_template
import logging
from django.db import transaction
from django.db.models import Subquery, OuterRef
from django.shortcuts import render
from .models import SalesForFabric
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.db.models import Count
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from joblib import dump, load
from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from sklearn.linear_model import LinearRegression
from django.db.models import Count, Max
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.generic import TemplateView
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.db.models import F
from geopy.geocoders import Nominatim
from .models import SalesForLocation
from django.core.serializers.json import DjangoJSONEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import random
import matplotlib.pyplot as plt
from django.views.generic import TemplateView
from django.shortcuts import render
from .models import CleanTrainingSets
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict
from datetime import datetime
import datetime as dt
from django.utils.crypto import get_random_string
# Create your views here.

@login_required
def dashboard(request):
    # Calculate the counts
    customer_count = Customer.objects.count()
    product_count = Product.objects.count()
    order_count = Order.objects.count()
    pending_order_count = Order.objects.filter(status='Pending').count()
    # Fetch the 5 most recent orders
    orders = Order.objects.all().order_by('-order_date')[:5]
    
    # Prepare lists for ordered products and ordered by
    ordered_products = []
    ordered_bys = []

    for order in orders:
        ordered_items = OrderItem.objects.filter(order=order)
        products = [item.product for item in ordered_items]
        customer = Customer.objects.get(user=order.customer)
        ordered_products.append(products)
        ordered_bys.append(customer)

    context = {
        'customer_count': customer_count,
        'product_count': product_count,
        'order_count': order_count,
        'pending_order_count': pending_order_count,
        'data': zip(ordered_products, ordered_bys, orders),
    }

    return render(request, 'dashboard.html', context)

def fchub_logout(request):
    logout(request)
    cache.clear()  # Clear the cache for all users
    return redirect('guest:index')

@login_required
def view_customer(request):
    customers = Customer.objects.all()   
    return render(request, 'view/customers.html', {'customers': customers})

@login_required
def view_order(request):
    # Get filter parameters from the request
    order_date_filter = request.GET.get('order_date')
    order_status_filter = request.GET.get('order_status')
    total_price_filter = request.GET.get('total_price')
    payment_type_filter = request.GET.get('payment_type')
    order_id_filter = request.GET.get('order_id')  # New filter parameter for Order ID

    # Start with an initial queryset of all orders
    orders = Order.objects.all()
    STATUS_CHOICES = Order.STATUS_CHOICES

    # Apply filters based on user input
    if order_id_filter:  # Check if the filter parameter is not empty
        # Filter orders where the order ID matches the input Order ID
        orders = orders.filter(order_number=order_id_filter)

    if order_date_filter:
        try:
            # Assuming 'order_date' is a DateField in the Order model
            # Convert the input date to a datetime.date object
            order_date_filter = datetime.strptime(order_date_filter, '%Y-%m-%d').date()
            # Filter orders where the order date matches the input date
            orders = orders.filter(order_date=order_date_filter)
        except ValueError:
            # Handle invalid date format gracefully (you can show an error message)
            pass

    if order_status_filter:  # Check if the filter parameter is not empty
        # Filter orders where the status matches the input status
        orders = orders.filter(status=order_status_filter)

    if total_price_filter == "low_to_high":
        # Assuming 'total_price' is a field in the Order model
        orders = orders.order_by('total_price')
    elif total_price_filter == "high_to_low":
        orders = orders.order_by('-total_price')

    if payment_type_filter:
        # Assuming 'payment_method' is a field in the Order model
        if payment_type_filter == 'Online Payment':
            # Correct the filter value to match your model
            orders = orders.filter(payment_method='Online Payment')
        elif payment_type_filter == 'Cash on Delivery (COD)':
            orders = orders.filter(payment_method='Cash on Delivery (COD)')

    # Annotate each order with the sum of total item prices
    orders = orders.annotate(total_item_price=Sum('order_items__item_total'))

    data = []

    for order in orders:
        ordered_items = order.order_items.all()
        ordered_by = Customer.objects.get(user=order.customer)
        data.append((ordered_items, ordered_by, order))

    return render(request, 'view/orders.html', {'data': data, 'status_choices': STATUS_CHOICES})


def calculate_count(setType, qty):
    # Define a dictionary to map set_type to its multiplier
    set_type_multipliers = {
        'Singles': 1,
        '3 in 1': 3,
        '4 in 1': 4,
        '5 in 1': 5,
    }

    # Calculate the count based on set_type and qty
    multiplier = set_type_multipliers.get(setType, 1)  # Default to 1 if set_type is not recognized
    return multiplier * qty


def get_fabric_material_count(fabric_name, color):
    fabric_count = FabricMaterial.objects.filter(
        fabric_name__iexact=fabric_name, color__iexact=color
    ).aggregate(total_count=Sum('fabric_fcount'))['total_count'] or 0
    return fabric_count


def get_material_count(type, name):
    material_count = Material.objects.filter(type=type, name__iexact=name).aggregate(total_count=Sum('count'))['total_count'] or 0
    return material_count
def check_product_availability(order_id):
    order_items = OrderItem.objects.filter(order_id=order_id)

    fabric_names = set()
    fabric_colors = set()

    for item in order_items:
        fabric_names.add(item.product.category.fabric.lower())
        fabric_colors.add(item.product.color.lower())
        if 'thread' in item.product.color.lower():
            color_parts = item.product.color.lower().split(' thread')
            color = color_parts[0].strip()
            fabric_colors.add(color.lower())

    fabric_count_total = 0

    distinct_curtain_fabric_names = CurtainIngredients.objects.values_list('fabric', flat=True).distinct()

    total_possible_qty = float('inf')  # Initialize variable to a high value to find the minimum possible creations

    for fabric_name in distinct_curtain_fabric_names:
        curtain_ingredients_for_name = CurtainIngredients.objects.filter(fabric=fabric_name)

        req_fabric_count = sum(ingredient.fabric_count for ingredient in curtain_ingredients_for_name)
        req_grommet_count = sum(ingredient.grommet_count for ingredient in curtain_ingredients_for_name)
        req_rings_count = sum(ingredient.rings_count for ingredient in curtain_ingredients_for_name)
        req_thread_count = sum(ingredient.thread_count for ingredient in curtain_ingredients_for_name)
        total_length_required = sum(ingredient.length for ingredient in curtain_ingredients_for_name)

        thread_sum = 0
        rings_sum = 0
        grommet_sum = 0

        for color in fabric_colors:
            fabric_count_total = FabricMaterial.objects.filter(fabric_name=fabric_name, color=color).aggregate(total_count=Sum('fabric_fcount'))['total_count'] or 0
            thread_sum += Material.objects.filter(type='Raw Materials Thread', name__iexact=f'{color.capitalize()} Thread').aggregate(total_thread=Sum('count'))['total_thread'] or 0
            rings_sum += Material.objects.filter(type='Raw Materials Attachments', name__iexact='Rings').aggregate(total_ring=Sum('count'))['total_ring'] or 0
            grommet_sum += Material.objects.filter(type='Raw Materials Attachments', name__iexact='Grommet Belt').aggregate(total_grommet=Sum('count'))['total_grommet'] or 0
            # Calculate quantity based on length for each creation

            # Compare required materials against available materials for this specific fabric type
            possible_creations = min(
                fabric_count_total // req_fabric_count,
                thread_sum // req_thread_count,
                rings_sum // req_rings_count,
                grommet_sum // req_grommet_count
            )
            total_possible_qty = min(total_possible_qty, possible_creations)
            print(total_possible_qty)

    total_fabric_materials = FabricMaterial.objects.all().count()
    total_materials = Material.objects.all().count()

    fabric_materials_total_qty = FabricMaterial.objects.aggregate(total_qty=Sum('fabric_fcount'))['total_qty'] or 0

    # Calculate possible quantity based on Materials
    thread_sum = Material.objects.filter(type='Raw Materials Thread').aggregate(total_thread=Sum('count'))['total_thread'] or 0
    rings_sum = Material.objects.filter(type='Raw Materials Attachments', name__iexact='Rings').aggregate(total_ring=Sum('count'))['total_ring'] or 0
    grommet_sum = Material.objects.filter(type='Raw Materials Attachments', name__iexact='Grommet Belt').aggregate(total_grommet=Sum('count'))['total_grommet'] or 0

    # Calculate the minimum possible creations based on both sources
    total_possible_qty_combined = min(
        fabric_materials_total_qty // req_fabric_count,
        thread_sum // req_thread_count,
        rings_sum // req_rings_count,
        grommet_sum // req_grommet_count
    )

    return {
        'fabric_count_total': fabric_count_total,
        'req_fabric_count': req_fabric_count,
        'req_grommet_count': req_grommet_count,
        'req_rings_count': req_rings_count,
        'req_thread_count': req_thread_count,
        'total_length_required': total_length_required,
        'total_possible_qty': total_possible_qty,
        'total_fabric_materials': total_fabric_materials,  # Total fabric materials count
        'total_materials': total_materials,  # Total materials count
        'total_possible_qty_fabric': fabric_materials_total_qty,
        'total_possible_qty_materials': min(thread_sum, rings_sum, grommet_sum),
        'total_possible_qty_combined': total_possible_qty_combined,

    }







from django.db import IntegrityError
@login_required
def update_status(request, order_id):
    order = Order.objects.get(id=order_id)
    customer_profile = order.customer

    # Get the current status of the order
    current_status = order.status
    print(current_status)
    # Define available status transitions based on the current status
    available_transitions = {
        'Pending': ['Order Confirmed'],
        'Order Confirmed': ['Out for Delivery'],
        'Out for Delivery': ['Delivered']
    }
    error_message = None
    allowed_choices = available_transitions.get(current_status, [])
    if request.method == 'POST':
        new_status = request.POST.get('new_status')

        # Check if the new status is allowed based on the current status
        if new_status in available_transitions.get(current_status, []):
            if new_status == 'Delivered':
                handle_order_confirmation(order)
            elif new_status == 'Delivered':
                handle_delivered_order(request, order)
                return redirect('fchub:orders')

            # Update the order status
            order.status = new_status
            order.save()
        else:
            # Handle invalid status change attempt here (e.g., show a message)
            print("Invalid status transition attempted.")
        
    ordered_products = OrderItem.objects.filter(order=order)
    ordered_fabrics = []
    fabric_names = []  # Store fabric names separately

    for item in ordered_products:
        product = item.product
        try:
            product_instance = Product.objects.get(name=product.name)
            inventory_quantity = product_instance.stock

            ordered_fabrics.append({
                'product': product_instance,
                'inventory_quantity': inventory_quantity
            })

            fabric_name = product_instance.category.fabric
            fabric_names.append(fabric_name)
            if item.quantity > inventory_quantity:
                error_message = "Could not create product due to low stock."
                break  # Break the loop on the first occurrence of low stock

        except Product.DoesNotExist:
            print(f"Product with name '{product.name}' does not exist")
    
    # Call the get_possible_combinations function here
    thread_colors = extract_colors_from_thread_materials()  # Extract colors from Raw Materials Thread
    possible_combinations = get_possible_combinations(order_id, thread_colors)

    # Create a list of dictionaries with necessary fields for the template
    combinations_data = []
    for combination in possible_combinations:
        data = {
            'Product': combination['product'].name,
            'Fabric': combination['ingredients']['fabric_name'],
            'Grommet': combination['ingredients']['grommet']['count'],
            'Rings': combination['ingredients']['rings']['count'],
            'Thread': combination['ingredients']['thread']['count'],
            'FabricColor': ', '.join([color.capitalize() for color in combination.get('matched_fabric_colors', [])]),
            'ThreadColor': ', '.join([material.name for material in combination.get('matched_materials', [])]),
            'fabrics_colors': combination.get('fabrics_colors', []),
            'PossibleProductCount': combination['possible_count'],
            

        }

        combinations_data.append(data)
        availability_data = check_product_availability(order_id)
    

    return render(request, 'update/update-status.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        'fabric_names': fabric_names,
        'ordered_fabrics': ordered_fabrics,
        'combinations_data': combinations_data,
        'req_fabric_count': availability_data['req_fabric_count'],
        'req_grommet_count': availability_data['req_grommet_count'],
        'req_rings_count': availability_data['req_rings_count'],
        'req_thread_count': availability_data['req_thread_count'],
        'total_length_required': availability_data['total_length_required'],
        'total_possible_qty': availability_data['total_possible_qty'],
        'total_fabric_materials': availability_data['total_fabric_materials'],
        'total_materials': availability_data['total_materials'],    
        'allowed_choices': allowed_choices,
        'total_possible_qty_combined': availability_data['total_possible_qty_combined'],  
        'error_message': error_message,
    })


def get_possible_combinations_with_count(order_id):
    order = Order.objects.get(id=order_id)
    ordered_products = OrderItem.objects.filter(order=order)

    available_materials = defaultdict(int)
    for material in Material.objects.all():
        available_materials[material.name] = material.count

    available_fabric_materials = defaultdict(int)
    for fabric_material in FabricMaterial.objects.all():
        available_fabric_materials[fabric_material.fabric_name] += fabric_material.fabric_fcount

    possible_combinations = []
    for item in ordered_products:
        product = item.product
        ingredients_needed = get_ingredients_needed(product)
        if can_produce_product(ingredients_needed, available_materials, available_fabric_materials):
            count = calculate_possible_product_count(product, ingredients_needed, available_materials, available_fabric_materials)
            
            possible_combinations.append({
                'product': product,
                'ingredients': ingredients_needed,
                'possible_count': count
            })

    return possible_combinations


def calculate_possible_product_count(product, ingredients_needed, available_materials, available_fabric_materials):
    min_possible_count = float('inf')  # Initialize with a large value

    for material, details in ingredients_needed.items():
        if material == 'fabric_name':
            continue  # Skip processing fabric name, handle other materials

        if details is not None and 'count' in details:  # Check if details is not None and 'count' key exists
            count_needed = details['count']

            if material in available_materials:
                available_count = available_materials[material]
                if available_count > 0:
                    possible_count = available_count // count_needed
                    if possible_count < min_possible_count:
                        min_possible_count = possible_count

    if 'fabric' in ingredients_needed:
        fabric_details = ingredients_needed['fabric']
        if fabric_details is not None and 'count' in fabric_details:  # Check if fabric_details is not None and 'count' key exists
            count_needed = fabric_details['count']
            fabric_name = ingredients_needed['fabric_name']

            if fabric_name in available_fabric_materials:
                available_fabric_count = available_fabric_materials[fabric_name]
                if available_fabric_count > 0:
                    possible_fabric_count = available_fabric_count // count_needed
                    if possible_fabric_count < min_possible_count:
                        min_possible_count = possible_fabric_count

    return min_possible_count



def get_ingredients_needed(product, thread_colors):
    product_category = product.category
    curtain_ingredients = CurtainIngredients.objects.filter(fabric=product_category.fabric)
    ingredients_needed = {
        'fabric_name': product_category.fabric,
        'fabric_color': None,  # Initialize fabric_color as None
        'fabric': None,  # Initialize fabric as None
        'grommet': None,  # Initialize grommet as None
        'rings': None,  # Initialize rings as None
        'thread': None,  # Initialize thread as None
        'length': None  # Initialize length as None
    }
    
    for ingredient in curtain_ingredients:
        # Extract color from the ingredient's fabric name
        fabric_name = ingredient.fabric.lower()
        fabric_color = None
        
        for color in thread_colors:
            if color in fabric_name:
                fabric_color = color
                break

        ingredients_needed = {
            'fabric_name': ingredient.fabric,
            'fabric_color': fabric_color,  # Include the extracted fabric color
            'fabric': {
                'count': ingredient.fabric_count,
                'unit': ingredient.fabric_unit
            },
            'grommet': {
                'count': ingredient.grommet_count,
                'unit': ingredient.grommet_unit
            },
            'rings': {
                'count': ingredient.rings_count,
                'unit': ingredient.rings_unit
            },
            'thread': {
                'count': ingredient.thread_count,
                'unit': ingredient.thread_unit
            },
            'length': {
                'count': ingredient.length,
                'unit': ingredient.length_unit
            }
        }
        

    return ingredients_needed




def get_possible_combinations(order_id, thread_colors):
    order = Order.objects.get(id=order_id)
    ordered_products = OrderItem.objects.filter(order=order)

    available_materials = defaultdict(int)
    for material in Material.objects.all():
        available_materials[material.name] = material.count

    available_fabric_materials = defaultdict(int)
    for fabric_material in FabricMaterial.objects.all():
        available_fabric_materials[fabric_material.fabric_name] += fabric_material.fabric_fcount

    possible_combinations = []
    for item in ordered_products:
        product = item.product
        color = product.color  # Assuming you've extracted the color from the product
        ordered_product_name = product.category.fabric  # Assuming you've extracted the fabric name from the product
        print('Fabric Name: ', ordered_product_name)
        print('Product Item: ', item)
        print('Product Color: ', color)

        # Loop through fabric materials to find a match
        fabric_materials = FabricMaterial.objects.all()
        matched_fabrics = []
        print('color (x)' ,color)
        
        matched_fabrics = set()
        matched_fabric_colors = set()
        fabrics_colors = []

        for fabric_material in fabric_materials:
            if fabric_material.fabric == ordered_product_name and fabric_material.color.lower() == color.lower():
                matched_fabrics.add(fabric_material)
                matched_fabric_colors.add(fabric_material.color)
                fabrics_colors.append(fabric_material.color.lower())  # Ensure lowercase consistency for comparison
                
        

       
        # Loop through materials to find a match based on color
        materials = Material.objects.filter(type='Raw Materials Thread')
        matched_materials = []

        for material in materials:
            if color.lower() in material.name.lower():
                matched_materials.append(material)

        ingredients_needed = get_ingredients_needed(product, thread_colors)

        if can_produce_product(ingredients_needed, available_materials, available_fabric_materials):
            possible_product_count = calculate_possible_product_count(
                product, ingredients_needed, available_materials, available_fabric_materials
            )
            possible_combinations.append({
                'product': product,
                'ingredients': ingredients_needed,
                'possible_count': possible_product_count,
                'matched_fabrics': matched_fabrics,
                'matched_materials': matched_materials,
                'fabrics_colors': fabrics_colors,  # Include 'fabrics_colors' in the combination data
            })

            print ('matched fabrics: ', matched_fabrics)
            print ('matched materials: ', matched_materials)
            print('matched_fabric_colors: ', matched_fabric_colors)
            print("Fabric Colors:", fabrics_colors)
    return possible_combinations


def can_produce_product(ingredients_needed, available_materials, available_fabric_materials):
    for material, details in ingredients_needed.items():
        if material == 'fabric_name':
            fabric_name = details
            continue  # Skip processing fabric name, handle other materials
            
        if details is not None and 'count' in details:  # Check if details is not None and 'count' key exists
            count_needed = details['count']
            if material in available_materials:
                if available_materials[material] < count_needed:
                    return False  # Not enough of this material in stock

    if 'fabric' in ingredients_needed:
        fabric_details = ingredients_needed['fabric']
        if fabric_details is not None and 'count' in fabric_details:  # Check if fabric_details is not None and 'count' key exists
            count_needed = fabric_details['count']
            fabric_unit = fabric_details['unit']
            fabric_name = ingredients_needed['fabric_name']
            
            if fabric_name in available_fabric_materials:
                if available_fabric_materials[fabric_name] < count_needed:
                    return False  # Not enough fabric material in stock
    return True


def extract_colors_from_thread_materials():
    thread_materials = Material.objects.filter(type='Raw Materials Thread')
    colors = set()

    for material in thread_materials:
        # Assuming the name has the color as the first word before space
        color = material.name.split(' ')[0].lower()
        colors.add(color.capitalize())  # Capitalize the extracted color

    return colors


def get_fabric_color(fabric_name):
    try:
        fabric = FabricMaterial.objects.filter(fabric=fabric_name).first()
        return fabric.color.capitalize() if fabric else 'Color Not Found'
    except FabricMaterial.DoesNotExist:
        return 'Color Not Found'

def get_thread_color(thread_colors, fabric_name):
    try:
        fabric_color = get_fabric_color(fabric_name)
        for color in thread_colors:
            if fabric_color.lower() in color.lower():
                return color.capitalize()
    except FabricMaterial.DoesNotExist:
        pass
    return 'Color Not Found'

# Function to identify fabric colors from ordered products
def get_fabric_colors_from_order(order_id):
    ordered_products = OrderItem.objects.filter(order_id=order_id)
    fabric_colors = set()

    for item in ordered_products:
        product = item.product
        fabric_name = product.category.fabric.lower()
        fabric_colors.add(fabric_name)

    return fabric_colors

# Function to match fabric colors with material colors
def match_fabric_color_with_materials(fabric_colors):
    fabric_material_colors = FabricMaterial.objects.values_list('fabric_color', flat=True)
    matched_colors = []

    for fabric_color in fabric_colors:
        for material_color in fabric_material_colors:
            if fabric_color in material_color.lower():
                matched_colors.append(material_color.capitalize())
                break

    return matched_colors

# Function to match thread colors with material colors
def match_thread_color_with_materials(thread_colors):
    material_thread_colors = Material.objects.filter(type='Raw Materials Thread').values_list('name', flat=True)
    matched_colors = []

    for thread_color in thread_colors:
        for material_color in material_thread_colors:
            if thread_color.lower() in material_color.lower():
                matched_colors.append(material_color.split()[0].capitalize())
                break

    return matched_colors


def handle_order_confirmation(order):
    order_items = order.order_items.all()

    products_to_update = []
    purchased_quantities = []

    for order_item in order_items:
        product = order_item.product
        products_to_update.append(product)
        purchased_quantities.append(order_item.quantity)

    with transaction.atomic():
        for idx, product in enumerate(products_to_update):
            purchased_quantity = purchased_quantities[idx]
            if purchased_quantity > product.stock:
                raise IntegrityError("Low stock. Cannot create the order due to insufficient inventory.")
            product.stock -= purchased_quantity
            product.save()

    # Return a success response if the order confirmation succeeds
    response_data = {
        'message': 'Order confirmed successfully.'
    }
    return JsonResponse(response_data)


def handle_delivered_order(request, order):
    existing_successful_order = SuccessfulOrder.objects.filter(success_order_id=order.order_number).first()

    if existing_successful_order:
        message = f"The order {order.order_number} has already been marked as delivered."
        return HttpResponse(message)
    
    customer_profile = Customer.objects.get(user=order.customer)
    fname = customer_profile.first_name
    lname = customer_profile.last_name
    customer_name = fname + " " + lname

    customer = order.customer
    address = order.shipping_address
    order_items = order.order_items.all()

    fabrics = ", ".join(order_item.product.category.fabric for order_item in order_items)
    setType = ", ".join(order_item.product.category.setType for order_item in order_items)
    colors = ", ".join(order_item.product.color for order_item in order_items)

    total_count = sum(order_item.quantity for order_item in order_items)
    total_count_for_set_type = sum(calculate_count(order_item.product.category.setType, order_item.quantity) for order_item in order_items)

    total_price = order.total_price

    successful_order = SuccessfulOrder(
        order_number=order.order_number,
        date=order.order_date.date(),
        location=address.city + ", " + address.province,
        name=customer_name,

        fabric=fabrics,
        setType=setType,
        color=colors,
        qty=total_count,
        count=total_count_for_set_type,
        price=total_price
    )

    last_5_order_number = order.order_number[-5:]
    customer_name = customer.first_name[:3]
    username = customer.username[:3]
    location = address.detailed_address[:3]
    successful_order.success_order_id = f'SuccessfulOrder-{last_5_order_number}-{customer_name}-{username}-{location}'
    successful_order.save()

    trainingsets = TrainingSets(
        date=order.order_date.date(),
        location=address.city + ", " + address.province,
        fabric=fabrics,
        setType=setType,
        color=colors,
        qty=total_count,
        count=total_count_for_set_type,
        total_price=total_price
    )
    trainingsets.save()




def render_to_pdf(template_path, context_dict):
    template = get_template(template_path)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def generate_invoice(request, order_id):
    # Ensure the user is an admin or has the necessary permissions
    if not request.user.is_staff:
        return HttpResponse("Permission denied", status=403)

    # Fetch the order with the given order_id
    order = get_object_or_404(Order, id=order_id)

    # Retrieve related customer, address, and order items
    customer = order.customer
    shipping_address = order.shipping_address
    order_items = order.order_items.all()

    # Calculate the total price for the order
    total_price = sum(item.item_total for item in order_items)

    # Access the user-related fields from the customer's profile
    customer_profile = Customer.objects.get(user=order.customer)
    customer_address = get_object_or_404(Address, customer=customer_profile)

    # Calculate VAT and total with VAT
    vat_rate = Decimal('0.12')
    vat = total_price * vat_rate
    with_vat = total_price + vat

    # Determine the shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0

    regions_three = ["National Capital Region (NCR)", "Region I (Ilocos Region)", "Region II (Cagayan Valley)",
                     "Region III (Central Luzon)", "Region IV-A (CALABARZON)", "Region V (Bicol Region)"]
    regions_four = ["Region VI (Western Visayas)", "Region VII (Central Visayas)", "Region VIII (Eastern Visayas)"]
    regions_five = ["Region IX (Zamboanga Peninsula)", "Region X (Northern Mindanao)",
                    "Region XI (Davao Region)", "Region XII (SOCCSKSARGEN)", "Region XIII (Caraga)",
                    "Cordillera Administrative Region (CAR)", "Autonomous Region in Muslim Mindanao (ARMM)"]

    if f_region in regions_three:
        shipping_fee = Decimal('300')
    elif f_region in regions_four:
        shipping_fee = Decimal('400')
    elif f_region in regions_five:
        shipping_fee = Decimal('500')

    # Calculate the total price including VAT and shipping fee
    total_price = with_vat + shipping_fee

    # Define context data to pass to the template
    context = {
        'customer': customer,
        'customer_profile': customer_profile,
        'shipping_address': shipping_address,
        'order': order,
        'order_items': order_items,
        'total_price': total_price,
        'vat': vat,
        'with_vat': with_vat,
        'shipping_fee': shipping_fee,
    }

    # Render the HTML template as a PDF
    pdf = render_to_pdf('view/invoice.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="invoice.pdf"'
        return response

    return HttpResponse("Error rendering PDF", status=500)

@login_required
def view_full_details(request, order_id):
    # Ensure the user is an admin or has the necessary permissions
    if not request.user.is_staff:
        return HttpResponse("Permission denied", status=403)

    # Fetch the order with the given order_id
    order = get_object_or_404(Order, id=order_id)

    # Retrieve related customer, address, and order items
    customer = order.customer
    shipping_address = order.shipping_address
    order_items = order.order_items.all()

    # Calculate the total price for the order
    total_price = sum(item.item_total for item in order_items)

    # Access the user-related fields from the customer's profile
    customer_profile = Customer.objects.get(user=order.customer)
    customer_address = get_object_or_404(Address, customer=customer_profile)

    # Calculate VAT and total with VAT
    vat_rate = Decimal('0.12')
    vat = total_price * vat_rate
    with_vat = total_price + vat

    # Determine the shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0

    regions_three = ["National Capital Region (NCR)", "Region I (Ilocos Region)", "Region II (Cagayan Valley)",
                     "Region III (Central Luzon)", "Region IV-A (CALABARZON)", "Region V (Bicol Region)"]
    regions_four = ["Region VI (Western Visayas)", "Region VII (Central Visayas)", "Region VIII (Eastern Visayas)"]
    regions_five = ["Region IX (Zamboanga Peninsula)", "Region X (Northern Mindanao)",
                    "Region XI (Davao Region)", "Region XII (SOCCSKSARGEN)", "Region XIII (Caraga)",
                    "Cordillera Administrative Region (CAR)", "Autonomous Region in Muslim Mindanao (ARMM)"]

    if f_region in regions_three:
        shipping_fee = Decimal('300')
    elif f_region in regions_four:
        shipping_fee = Decimal('400')
    elif f_region in regions_five:
        shipping_fee = Decimal('500')

    # Calculate the total price including VAT and shipping fee
    total_price = with_vat + shipping_fee

    # Define context data to pass to the template
    context = {
        'customer': customer,
        'customer_profile': customer_profile,
        'shipping_address': shipping_address,
        'order': order,
        'order_items': order_items,
        'total_price': total_price,
        'vat': vat,
        'with_vat': with_vat,
        'shipping_fee': shipping_fee,
    }

    return render(request, 'view/full-details.html', context)




@login_required
def view_product(request):
    # Get the selected sorting option from the GET request
    sort_option = request.GET.get('sort')

    # Default to sorting by price low to high
    if sort_option == 'high_to_low':
        products = Product.objects.all().order_by('-price')
    else:
        products = Product.objects.all().order_by('price')

    return render(request, 'view/products.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('fchub:products')  # Adjust this URL name as needed
    else:
        form = ProductForm()
    return render(request, 'add/add-product.html', {'form': form})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    
    if request.method == 'POST':
        product.delete()
        return redirect('fchub:products')  # Redirect to the list of products after deleting
    
    return render(request, 'delete/delete-product.html', {'product': product})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('fchub:products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'edit/edit-product.html', {'form': form})


@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('fchub:category')
    else:
        form = CategoryForm()
    return render(request, 'add/add-category.html', {'form': form})


@login_required
def edit_category(request, category_id):
    category = Category.objects.get(id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('fchub:category')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'edit/edit-category.html', {'form': form, 'category': category})

@login_required
def delete_category(request, category_id):
    category = Category.objects.get(id=category_id)
    category.delete()
    return redirect('fchub:category')

@login_required
def category_list(request):
    categories = Category.objects.all()
    fabric_choices = Category.FABRIC_CHOICES
    set_type_choices = Category.SET_TYPE_CHOICES

    fabric_filter = request.GET.get('fabric')
    set_type_filter = request.GET.get('set_type')

    if fabric_filter:
        categories = categories.filter(fabric=fabric_filter)
    if set_type_filter:
        categories = categories.filter(setType=set_type_filter)

    return render(request, 'view/category.html', {
        'categories': categories,
        'fabric_choices': fabric_choices,
        'set_type_choices': set_type_choices,
        'selected_fabric': fabric_filter,
        'selected_set_type': set_type_filter,
    })


@login_required
def view_materials(request):
    regular_materials = Material.objects.all()
    fabric_materials = FabricMaterial.objects.all()
    
    return render(
        request,
        'view/materials.html',
        {'regular_materials': regular_materials, 'fabric_materials': fabric_materials}
    )


def choose_material_type(request):
    return render(request, 'add/choose-material-type.html')

@login_required
def add_regular_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name'].lower()
            custom_material_id = name[:2] + datetime.now().strftime("%y%m%d%H")
            
            # Generate a unique ID based on name and random string
            random_string = get_random_string(length=2)
            custom_material_id = f"{name[:2]}{random_string}"

            if Material.objects.filter(name__iexact=name).exists() or Material.objects.filter(Custom_material_id=custom_material_id).exists():
                messages.error(request, 'Material with this name or custom material ID already exists.')
            else:
                material = form.save(commit=False)
                material.name = name
                material.Custom_material_id = custom_material_id
                material.save()
                messages.success(request, 'Material saved successfully.')
                return redirect('fchub:materials')

        else:
            messages.error(request, 'Form is not valid.')

    else:
        form = MaterialForm()

    return render(request, 'add/add-regular-material.html', {'form': form})


def add_fabric_material(request):
    if request.method == 'POST':
        form = FabricMaterialForm(request.POST)

        if form.is_valid():
            fabric_material = form.save(commit=False)
            fabric_name = fabric_material.fabric_name.lower()

            if FabricMaterial.objects.filter(fabric_name__iexact=fabric_name).exists():
                # Fabric material with this name already exists, show an error message
                messages.error(request, 'Fabric material with this name already exists.')
            else:
                # Name doesn't exist, proceed to save the fabric material
                fabric_material.save()
                messages.success(request, 'Fabric material saved successfully.')
                return redirect('fchub:materials')

        else:
            messages.error(request, 'Form is not valid.')

    else:
        form = FabricMaterialForm()

    return render(request, 'add/add-fabric-material.html', {'form': form})


@login_required
def delete_regular_material(request, pk):
    material = get_object_or_404(Material, id=pk)
    
    if request.method == 'POST':
        material.delete()
        return redirect('fchub:materials')  # Redirect to the list of materials after deleting
    
    return render(request, 'delete/delete-regular-material.html', {'material': material})

@login_required
def edit_regular_material(request, material_id):
    material = Material.objects.get(id=material_id)

    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('fchub:materials')
    else:
        form = MaterialForm(instance=material)

    return render(request, 'edit/edit-regular-material.html', {'form': form})

@login_required
def delete_fabric_material(request, pk):
    fabric_material = get_object_or_404(FabricMaterial, id=pk)
    
    if request.method == 'POST':
        fabric_material.delete()
        return redirect('fchub:materials')  # Redirect to the list of materials after deleting
    
    return render(request, 'delete/delete-fabric-material.html', {'fabric_material': fabric_material})

@login_required
def edit_fabric_material(request, material_id):
    fabric_material = FabricMaterial.objects.get(id=material_id)

    if request.method == 'POST':
        form = FabricMaterialForm(request.POST, instance=fabric_material)
        if form.is_valid():
            form.save()
            return redirect('fchub:materials')
    else:
        form = FabricMaterialForm(instance=fabric_material)

    return render(request, 'edit/edit-fabric-material.html', {'form': form})








@login_required
def view_purchase(request):
    fabric_type = request.GET.get('fabric_type')
    payment = request.GET.get('payment')
    price = request.GET.get('price')
    color = request.GET.get('color')
    product_tag = request.GET.get('product_tag')
    setType = request.GET.get('setType')
    month_of_purchase = request.GET.get('month_of_purchase')
    qty = request.GET.get('qty')
    count = request.GET.get('count')

    purchases = Tracker.objects.all()

    if fabric_type:
        purchases = purchases.filter(fabric_type=fabric_type)
    if payment:
        purchases = purchases.filter(payment=payment)
    if price == 'low_to_high':
        purchases = purchases.order_by('price')
    elif price == 'high_to_low':
        purchases = purchases.order_by('-price')
    if color:
        purchases = purchases.filter(color=color)
    if product_tag:
        purchases = purchases.filter(product_tag=product_tag)
    if setType:
        purchases = purchases.filter(setType=setType)
    if month_of_purchase:
        purchases = purchases.filter(month_of_purchase=month_of_purchase)
    if qty:
        purchases = purchases.filter(qty=qty)
    if count == 'low_to_high':
        purchases = purchases.order_by('count')
    elif count == 'high_to_low':
        purchases = purchases.order_by('-count')

    return render(request, 'view/track-purchase.html', {'purchases': purchases})


# Add a new purchase record
@login_required
def add_purchase(request):
    if request.method == 'POST':
        form = TrackerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('fchub:track-purchase')
    else:
        form = TrackerForm()
    return render(request, 'add/add-purchase.html', {'form': form})

# Edit an existing purchase record
@login_required
def edit_purchase(request, purchase_id):
    purchase = Tracker.objects.get(id=purchase_id)
    if request.method == 'POST':
        form = TrackerForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            return redirect('fchub:track-purchase')
    else:
        form = TrackerForm(instance=purchase)
    return render(request, 'edit/edit-purchase.html', {'form': form, 'purchase': purchase})

# Delete a purchase record
@login_required
def delete_purchase(request, purchase_id):
    purchase = Tracker.objects.get(id=purchase_id)
    
    if request.method == 'POST':
        purchase.delete()
        return redirect('fchub:track-purchase')  # Redirect to the list of purchases after deleting
    
    return render(request, 'delete/delete-purchase.html', {'purchase': purchase})







import os
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.shortcuts import render
from google.oauth2 import credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def get_gmail_labels():
    # Initialize the Gmail API using OAuth2 credentials
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']

    flow = InstalledAppFlow.from_client_config({
        "web": {
            "client_id": "1033173894917-o3hdqj0t915jad8ev98smgdvp6eptogn.apps.googleusercontent.com",
            "client_secret": "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",
            "auth_uri": "https://accounts.google.com/",
            "token_uri": "https://oauth2.googleapis.com/token",
        },
    }, scopes=scopes)

    creds = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=creds)

    # List Gmail labels
    labels = service.users().labels().list(userId='me').execute()
    
    return labels['labels']

@login_required
def view_manage_business(request):
    try:
        active = request.user.fleekyadmin
    except FleekyAdmin.DoesNotExist:
        active = None  # Handle the case when FleekyAdmin is missing

    # Get Gmail labels using the function
    #gmail_labels = get_gmail_labels()
    #'gmail_labels': gmail_labels
    return render(request, 'manage-business/manage-business.html', {'active': active, })


def parse_csv_data(csv_file):
    csv_data = []

    try:
        # Assuming csv_file is a File object
        # Read the CSV content from the file
        csv_content = csv_file.read().decode('utf-8')

        # Create a CSV reader
        csv_reader = csv.reader(io.StringIO(csv_content))

        # Limit the number of samples to 6
        sample_count = 0

        # Iterate through the rows and add them to csv_data
        for row in csv_reader:
            csv_data.append(row)
            sample_count += 1

            if sample_count >= 6:
                break

    except Exception as e:
        # Handle any exceptions that may occur during parsing
        # You can log the error or raise an appropriate exception
        pass

    return csv_data

ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.xlsm', '.xlsb', '.xltx', '.xltm', '.xlam', '.csv', '.ods', '.xml', '.txt', '.prn', '.dif', '.slk', '.htm', '.html', '.dbf', '.json'}


def upload_csv(request):
    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']

            # Check the file extension
            file_extension = os.path.splitext(csv_file.name)[1].lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                # Add an error message and reload the page
                messages.error(request, f'Unsupported file type: {file_extension}. Please upload a valid file.')
                return redirect('fchub:upload-csv')

            try:
                # Read the CSV content from the file
                csv_content = csv_file.read().decode('utf-8')

                # Create a Csv object and save it with a unique name
                csv = Csv(csv_file=csv_file)
                csv.save()

                # Rename the file with a unique name
                csv.file_name = f'csv-{csv.id}-{csv.uploaded_at.strftime("%Y%m%d")}'
                csv.save()

                # Add a success message
                messages.success(request, 'CSV file uploaded successfully.')
            except Exception as e:
                # Handle any exceptions that may occur during parsing
                # You can log the error or raise an appropriate exception
                messages.error(request, 'Error processing the uploaded CSV file.')

    form = CsvUploadForm()

    # Get all uploaded CSV files
    csv_files = Csv.objects.all()

    # Fetch the most recent CSV entry
    most_recent_csv = Csv.objects.order_by('-uploaded_at').first()

    # Check if there is no uploaded file
    if not most_recent_csv:
        messages.info(request, 'Please upload a CSV file first.')  # Add this message
    else:
        # Parse the most recent CSV data (assuming it's a CSV string) into a list of lists
        most_recent_csv.csv_data = parse_csv_data(most_recent_csv.csv_file)

    recent_csv_files = Csv.objects.order_by('-uploaded_at')[:5]

    return render(request, 'manage-business/csv-template.html', {'form': form, 'recent_csv_files': recent_csv_files, 'csv_files': csv_files, 'most_recent_csv': most_recent_csv})

def delete_csv(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        try:
            csv_file = Csv.objects.get(id=file_id)
            if not csv_file.csv_file.closed:
                csv_file.csv_file.close()  # Close the file if it's open
            # Delete the Csv object from the database
            csv_file.delete()
        except Csv.DoesNotExist:
            # Handle the case where the CSV file does not exist
            pass

    return redirect('fchub:upload-csv')  # Redirect to the page where CSV files are listed


def parse_csv_for_migration(csv_content):
    # Create a list to store the CSV data
    data = []

    # Create a CSV reader
    csv_reader = csv.reader(io.StringIO(csv_content))

    # Skip the header row (if present)
    next(csv_reader, None)

    for row in csv_reader:
        data.append(row)

    return data

def migrate_csv_data(csv_data):
    try:
        # Iterate through the rows and create CsvData objects
        for row in csv_data:
            CsvData.objects.create(
                year=row[0],
                month=row[1],
                day=row[2],
                location=row[3],
                customerName=row[4],
                fabric=row[5],
                setType=row[6],
                color=row[7],
                quantity=row[8],
                count=row[9],
                price=row[10]
            )

    except Exception as e:
        # Handle any exceptions that may occur during migration
        print(f"Error during migration: {str(e)}")

def migrate_csv(request, csv_id):
    # Retrieve the Csv object with the provided ID
    csv = get_object_or_404(Csv, id=csv_id)

    # Ensure that csv.csv_file is a string by reading its content
    csv_content = csv.csv_file.read().decode('utf-8')

    # Parse the CSV content into a list of lists
    csv_data = parse_csv_for_migration(csv_content)

    if isinstance(csv_data, list):
        # Migrate CSV data to CsvData model
        migrate_csv_data(csv_data)

        # Redirect to the main CSV upload page with a success message
        messages.success(request, 'CSV data migrated to the database.')
        return redirect('fchub:upload-csv')
    else:
        # Handle the case where parse_csv_for_migration returned something other than a list
        return HttpResponseBadRequest('Invalid CSV data format')

def view_csv(request, file_id):
    # Fetch the CSV file from the database
    csv_file = get_object_or_404(Csv, id=file_id)

    # Parse the CSV file content
    csv_data = []
    try:
        csv_text = csv_file.csv_data
        csv_reader = csv.reader(csv_text.splitlines())
        for row in csv_reader:
            csv_data.append(row)
    except Exception as e:
        # Handle any exceptions (e.g., invalid CSV format)
        pass  # You should create an error template

    return render(request, 'csv-template.html', {'csv_data': csv_data, 'most_recent_csv': None})



def get_csv_data(request, file_id):
    try:
        # Retrieve the CSV file with the specified file_id
        csv_file = get_object_or_404(Csv, id=file_id)

        # Read the content from the csv_file field
        with open(csv_file.csv_file.path, 'rb') as file:
            csv_data = file.read()

        # You can customize the response content type based on your CSV data format
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{csv_file.file_name}.csv"'
        return response
    except Csv.DoesNotExist:
        # Handle the case where the CSV file does not exist
        return HttpResponse("CSV file not found.", status=404)


@login_required
def users_admins(request):
    admins = FleekyAdmin.objects.all()
    return render(request, 'view/users-admin.html', {'admins': admins})

@login_required
def add_admin(request):
    if request.method == 'POST':
        # Create instances of UserCreationForm and FleekyAdminForm
        user_form = UserCreationForm(request.POST)
        admin_form = FleekyAdminForm(request.POST)
        
        if user_form.is_valid() and admin_form.is_valid():
            # Save the user form to create a new user
            user = user_form.save()
            
            # Create a FleekyAdmin instance and link it to the user
            admin = admin_form.save(commit=False)
            admin.user = user
            admin.save()
            
            return redirect('fchub:users-admins')  # Redirect to the list of admins
    else:
        user_form = UserCreationForm()
        admin_form = FleekyAdminForm()
    
    return render(request, 'add/user-admin.html', {'user_form': user_form, 'admin_form': admin_form})

@login_required
def delete_admin(request, pk):
    admin = get_object_or_404(FleekyAdmin, pk=pk)
    admin.delete()
    return redirect('fchub:users-admins')  # Redirect to the list of admins after deleting


@login_required
def successful_orders(request):
    successful_orders = SuccessfulOrder.objects.all()
    return render(request, 'view/successful-orders.html', {'successful_orders': successful_orders})


@login_required
def download_successful_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="successful_orders.csv"'

    writer = csv.writer(response)
    writer.writerow(['Year', 'Month', 'Day', 'Location', 'Name', 'Fabric', 'Set', 'Color', 'Qty', 'Count', 'Price'])

    successful_orders = SuccessfulOrder.objects.all()

    for order in successful_orders:
        year = order.date.year
        month = calendar.month_name[order.date.month]  # Convert month to string
        day = order.date.day
        writer.writerow([year, month, day, order.location, order.name, order.fabric, order.setType, order.color, order.qty, order.count, order.price])

    return response




MONTH_MAPPING = {
    'January': '01',
    'February': '02',
    'March': '03',
    'April': '04',
    'May': '05',
    'June': '06',
    'July': '07',
    'August': '08',
    'September': '09',
    'October': '10',
    'November': '11',
    'December': '12',
}
@login_required
def view_fchub_model(request):
    combined_data = SalesForWebData.objects.all()
    purchase_data = Tracker.objects.all()
    successful_orders = SuccessfulOrder.objects.all()
    raw_training_sets = TrainingSets.objects.all()
    cleaned_training_sets = CleanTrainingSets.objects.all()
    # Add the following lines to retrieve data for the new models
    sales_for_fabric_data = SalesForFabric.objects.all()
    sales_for_category_data = SalesForCategory.objects.all()
    sales_for_location_data = SalesForLocation.objects.all()
    sales_for_color_data = SalesForColor.objects.all()

    parsed_combined_data = []

    for data in combined_data:
        if data.date:
            date_obj = datetime.strptime(data.date.strftime("%Y-%m-%d"), "%Y-%m-%d")
            data.date = date_obj.strftime("%B")  # Update the 'date' field to the month
        parsed_combined_data.append(data)

    context = {
        'parsed_combined_data': parsed_combined_data,
        'purchase_data': purchase_data,
        'successful_orders': successful_orders,
        'sales_for_fabric_data': sales_for_fabric_data,
        'sales_for_category_data': sales_for_category_data,
        'sales_for_location_data': sales_for_location_data,
        'sales_for_color_data': sales_for_color_data,
        'raw_training_sets':raw_training_sets,
        'cleaned_training_sets':cleaned_training_sets,
    }

    return render(request, 'manage-business/fchub-data-model.html', context)


def migrate_fchub_data(request):
    try:
        combined_data = []

        # Retrieve data from the SuccessfulOrder and Tracker models
        successful_orders = SuccessfulOrder.objects.all()
        #tracker_data = Tracker.objects.all()

        # Define the fields to process
        fields = ["fabric", "color", "setType"]

        # Create a dictionary to group data by price
        price_groups = {}

        # Iterate through the data
        for data in successful_orders:
            price = data.price
            if price not in price_groups:
                price_groups[price] = {
                    field: data_field.split(", ") for field, data_field in zip(fields, [data.fabric, data.color, data.setType])
                }
            else:
                for field, data_field in zip(fields, [data.fabric, data.color, data.setType]):
                    price_groups[price][field] += data_field.split(", ")

        for price, group in price_groups.items():
            num_combinations = len(group[fields[0]])
            
            for i in range(num_combinations):
                sales_data = SalesForWebData()
                sales_data.fabric_type = group["fabric"][i]
                sales_data.date = data.date
                sales_data.color = group["color"][i]
                sales_data.set_type = group["setType"][i]
                sales_data.price = price if i == 0 else None  # Set price only for the first row
                combined_data.append(sales_data)


        # Save the combined data to the SalesForWebData model
        SalesForWebData.objects.bulk_create(combined_data)

        messages.success(request, 'Combined data migrated successfully.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    # Redirect to the 'fchub-data-model' view
    return HttpResponseRedirect(reverse('fchub:fchub-data-model'))





def delete_all_data(request):
    # Delete all records from the SalesForWebData model
    SalesForWebData.objects.all().delete()

    return redirect('fchub:fchub-data-model')


def delete_clean_all_data(request):
    # Delete all records from the SalesForWebData model
    CleanTrainingSets.objects.all().delete()

    return redirect('fchub:fchub-data-model')


def delete_fabrics_data(request):
    # Delete all records from the SalesForWebData model
    SalesForFabric.objects.all().delete()

    return redirect('fchub:fchub-data-model')

def delete_setType_data(request):
    # Delete all records from the SalesForWebData model
    SalesForCategory.objects.all().delete()
    return redirect('fchub:fchub-data-model')

def delete_color_data(request):
    # Delete all records from the SalesForWebData model
    SalesForColor.objects.all().delete()
    return redirect('fchub:fchub-data-model')

def delete_location_data(request):
    # Delete all records from the SalesForWebData model
    SalesForLocation.objects.all().delete()
    return redirect('fchub:fchub-data-model')

def migrate_fabric_data(request):
    try:
        combined_fabric = []

        combined_data = SalesForWebData.objects.all()

        # Iterate through SalesForWebData data
        for data in combined_data:
            # For each SalesForWebData instance, create a SalesForFabric instance
            sales_data = SalesForFabric()
            sales_data.fabric = data.fabric_type  # Correct the field name to 'fabric'
            sales_data.date = data.date

            # Extract the month from the date
            sales_data.month = data.date.strftime('%B')  # %B gives the full month name

            # Save the instance to the combined_fabric list
            sales_data.save()
            combined_fabric.append(sales_data)

        messages.success(request, 'Combined data migrated successfully.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    # Redirect to the 'fchub-data-model' view
    return HttpResponseRedirect(reverse('fchub:fchub-data-model'))

def migrate_category_data(request):
    try:
        combined_category = []

        combined_data = SalesForWebData.objects.all()

        # Iterate through SalesForCategory data
        for data in combined_data:
            # For each SalesForCategory instance, create a SalesForFabric instance
            sales_data = SalesForCategory()
            sales_data.set_tag = data.set_type
            sales_data.date = data.date

            # Extract the month from the date
            sales_data.month = data.date.strftime('%B')  # %B gives the full month name

            # Save the instance to the combined_fabric list
            sales_data.save()
            combined_category.append(sales_data)

        messages.success(request, 'Category data migrated successfully.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    # Redirect to the 'fchub-data-model' view (or update this as needed)
    return HttpResponseRedirect(reverse('fchub:fchub-data-model'))

def migrate_location_data(request):
    try:
        # Create a set to keep track of processed combinations
        processed_combinations = set()

        combined_location = []

        successful_orders = SuccessfulOrder.objects.all()
        #tracker_data = Tracker.objects.all()

        # Define the fields to process
        fields = ["fabric", "color", "setType"]

        for data in successful_orders:
            location = data.location  # Change this to the relevant field
            if location not in processed_combinations:
                location_data = {
                    field: data_field.split(", ") for field, data_field in zip(fields, [data.fabric, data.color, data.setType])
                }
                num_combinations = len(location_data[fields[0]])
                
                for i in range(num_combinations):
                    fabric = location_data["fabric"][i]
                    color = location_data["color"][i]
                    set_type = location_data["setType"][i]

                    # Check if this combination has already been processed
                    combination_key = f"{fabric}-{color}-{set_type}-{location}"
                    if combination_key not in processed_combinations:
                        sales_data = SalesForLocation()
                        sales_data.date = data.date
                        sales_data.fabric = fabric
                        sales_data.color = color
                        sales_data.set_type = set_type
                        sales_data.location = location

                        combined_location.append(sales_data)
                        # Mark this combination as processed
                        processed_combinations.add(combination_key)

        SalesForLocation.objects.bulk_create(combined_location)
        
        sales = SalesForLocation.objects.all()

        geolocator = Nominatim(user_agent="sales_app")  # Create a geocoder object

        # Iterate through sales data and geocode the location names
        for sale in sales:
            location = sale.location
            if location:
                location_info = geolocator.geocode(location)
                if location_info:
                    sale.latitude = location_info.latitude
                    sale.longitude = location_info.longitude
                    sale.save()
        messages.success(request, 'Location data migrated successfully.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    # Redirect to the 'fchub-data-model' view or adjust the name accordingly
    return HttpResponseRedirect(reverse('fchub:fchub-data-model'))


def migrate_color_data(request):
    try:
        combined_color = []

        successful_orders = SuccessfulOrder.objects.all()

        for order in successful_orders:
            fabric = order.fabric
            color = order.color

            # Split the data fields by comma and whitespace
            fabric_values = fabric.split(", ")
            color_values = color.split(", ")

            # Ensure that both fabric and color have the same number of values
            num_combinations = min(len(fabric_values), len(color_values))

            for i in range(num_combinations):
                sales_data = SalesForColor()
                sales_data.fabric = fabric_values[i]
                sales_data.color = color_values[i]
                sales_data.date = order.date

                combined_color.append(sales_data)

        # Save the combined data to the SalesForColor model
        SalesForColor.objects.bulk_create(combined_color)

        messages.success(request, 'Color data migrated successfully.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    # Redirect to the view you want (adjust the name accordingly)
    return HttpResponseRedirect(reverse('fchub:fchub-data-model'))

def migrate_training_data(request):
    try:
        processed_combinations = set()
        combined_training_data = []

        training_data = TrainingSets.objects.all()

        for data in training_data:
            location = data.location
            location_data = {
                'fabric': data.fabric.split(', '),
                'color': data.color.split(', '),
                'setType': data.setType.split(', '),
            }
            num_combinations = len(location_data['fabric'])

            for i in range(num_combinations):
                fabric = location_data['fabric'][i]
                color = location_data['color'][i]
                set_type = location_data['setType'][i]

                combination_key = f"{fabric}-{color}-{set_type}-{location}"
                if combination_key not in processed_combinations:
                    clean_training_data = CleanTrainingSets(
                        date=data.date,
                        location=location,
                        fabric=fabric,
                        setType=set_type,
                        color=color,
                        qty=data.qty,
                        count=data.count,
                        total_price=data.total_price
                    )

                    combined_training_data.append(clean_training_data)
                    processed_combinations.add(combination_key)


        CleanTrainingSets.objects.bulk_create(combined_training_data)
        messages.success(request, 'Location data migrated successfully.')
    except Exception as e:
        messages.error(request, f'Error: {e}')
        print(f"Error: {e}")  # Print the error message

    return redirect('fchub:fchub-data-model')




# View to list sales and generate chart data
def sales_for_fabric_list(request):
    sales = SalesForFabric.objects.all()

    # Prepare data for charts
    fabric_counts = SalesForFabric.objects.values('fabric').annotate(count=Count('fabric'))
    fabric_labels = [item['fabric'] for item in fabric_counts]
    fabric_counts = [item['count'] for item in fabric_counts]

    # Prepare bar graph data
    bar_data = {
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'fabrics': fabric_labels,
        'sales_data': {}
    }

    for fabric in fabric_labels:
        fabric_data = SalesForFabric.objects.filter(fabric=fabric).values('date__month').annotate(count=Count('date__month'))
        sales_by_month = [0] * 12
        for item in fabric_data:
            sales_by_month[item['date__month'] - 1] = item['count']
        bar_data['sales_data'][fabric] = sales_by_month

    context = {
        'sales': sales,
        'fabric_labels': fabric_labels,
        'fabric_counts': fabric_counts,
        'bar_data': bar_data,
    }

    return render(request, 'view/sales-per-product.html', context)








class SalesForCategoryView(TemplateView):
    template_name = 'view/sales-per-category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales = SalesForCategory.objects.all()

        # Prepare data for charts
        category_counts = SalesForCategory.objects.values('set_tag').annotate(count=Count('set_tag'))
        category_labels = [item['set_tag'] for item in category_counts]
        category_counts = [item['count'] for item in category_counts]

        # Prepare bar graph data based on months
        bar_data = {
            'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'categories': category_labels,
            'sales_data': {}
        }

        for category in category_labels:
            category_data = SalesForCategory.objects.filter(set_tag=category).annotate(
                month=TruncMonth('date')
            ).values('month').annotate(count=Count('month')).order_by('month')
            sales_by_month = [0] * 12
            for item in category_data:
                month = item['month'].strftime('%b')  # Format the month as abbreviated name
                index = bar_data['months'].index(month)
                sales_by_month[index] = item['count']
            bar_data['sales_data'][category] = sales_by_month

        context['sales'] = sales
        context['category_labels'] = category_labels
        context['category_counts'] = category_counts
        context['bar_data'] = bar_data

        return context

class SalesForColorView(TemplateView):
    template_name = 'view/sales-per-color.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales = SalesForColor.objects.all()

        # Prepare data for charts
        color_counts = SalesForColor.objects.values('color').annotate(count=Count('color'))
        color_labels = [item['color'] for item in color_counts]
        color_counts = [item['count'] for item in color_counts]

        # Prepare bar graph data based on months
        color_bar_data = {
            'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'colors': color_labels,
            'sales_data': {}
        }

        for color in color_labels:
            color_data = SalesForColor.objects.filter(color=color).annotate(
                month=TruncMonth('date')
            ).values('month').annotate(count=Count('month')).order_by('month')
            sales_by_month = [0] * 12
            for item in color_data:
                month = item['month'].strftime('%b')  # Format the month as an abbreviated name
                index = color_bar_data['months'].index(month)
                sales_by_month[index] = item['count']
            color_bar_data['sales_data'][color] = sales_by_month

        context['sales'] = sales
        context['color_labels'] = color_labels
        context['color_counts'] = color_counts
        context['color_bar_data'] = color_bar_data

        return context


from collections import Counter, defaultdict

def sales_for_location_list(request):
    sales = SalesForLocation.objects.all()

    sales_data = []
    locations = []
    fabrics = []
    dates = []
    set_types = []

    location_counts = Counter()  # Count the occurrences of each location

    for sale in sales:
        location = sale.location
        sales_data.append({
            'location': location,
            'latitude': sale.latitude,
            'longitude': sale.longitude,
            'fabric': sale.fabric,
            'dates': sale.date.strftime('%B'),  # Convert date to the full month name
            'set_type': sale.set_type,
        })

        locations.append(location)
        fabrics.append(sale.fabric)
        dates.append(sale.date.strftime('%B'))
        set_types.append(sale.set_type)

        location_counts[location] += 1  # Update the location count

    context = {
        'sales_data': json.dumps(sales_data, cls=DjangoJSONEncoder),
        'locations': json.dumps(locations),
        'fabrics': json.dumps(fabrics),
        'dates': json.dumps(dates),
        'set_types': json.dumps(set_types),
        'location_counts': dict(location_counts),  # Provide the location counts as a dictionary
        'sales_data': sales_data,
    }

    return render(request, 'view/sales-per-location.html', context)

import matplotlib
matplotlib.use('agg')
class TopSellingModelTrainer(TemplateView):
    template_name = 'manage-business/train-top-selling.html'

    def get(self, request):
        return render(request, self.template_name, {'message': None, 'top_selling_dataset': None, 'raw_data': None, 'training_reports': None})

    def post(self, request):
        data = CleanTrainingSets.objects.values()
        df = pd.DataFrame(data)

        top_selling_datasets = self.calculate_quantity(df)
        cleaned_data = self.clean_data(df)
        trained_models, maes = self.train_model(cleaned_data)

        # Calculate training reports
        accuracy = self.calculate_accuracy(cleaned_data, trained_models)
        model_type = 'Linear Regression'  # You can set the actual model type here

        # Prepare training reports
        training_reports = {
            'accuracy': accuracy,
            'model_type': model_type,
        }

        context = {
            'message': "Success: Quantity calculated for each combination of fabric, set type, and color",
            'top_selling_dataset': top_selling_datasets,
            'raw_data': data,
            'trained_models': trained_models,
            'maes': maes,
            'training_reports': training_reports,
        }

        return render(request, self.template_name, context)

    def calculate_quantity(self, df):
        quantity_by_combination = []

        # Group the data by unique combinations of 'fabric', 'setType', and 'color'
        combinations = df.groupby(['fabric', 'setType', 'color'])

        for combination, data in combinations:
            total_quantity = data['qty'].sum()  # Calculate the total quantity for the combination
            quantity_by_combination.append({
                'fabric': combination[0],
                'setType': combination[1],
                'color': combination[2],
                'qty': total_quantity
            })

        return quantity_by_combination


    def clean_data(self, df):
        label_encoders = self.get_label_encoders(df)

        print("Columns in DataFrame:")
        print(df.columns)

        for col in ['fabric', 'setType', 'color']:
            if col in df.columns:
                df[col] = label_encoders[col].transform(df[col])
            else:
                # Handle the case when the column is not found
                print(f"Column '{col}' not found in the dataset")

        return df

    def train_model(self, df):
        models = {}
        model_reports = {}  # To store model training reports

        for col in ['fabric', 'setType', 'color']:
            group = df.groupby(col)
            for group_name, group_data in group:
                if len(group_data) < 2:
                    print(f"Skipping {col} group '{group_name}' due to insufficient data.")
                    continue

                X = group_data[['fabric', 'setType', 'color', 'qty']]
                y = group_data['qty']

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                model = LinearRegression()
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)

                group_data['predicted_qty'] = model.predict(X)

                # Calculate R-squared value (coefficient of determination)
                r_squared = r2_score(y_test, y_pred)

                model_key = f'{col}_{group_name}'
                models[model_key] = (f'qty for {col} {group_name}', mae)
                
                # Store the training report for the model
                model_reports[model_key] = {
                    'model_type': 'Linear Regression',
                    'r_squared': r_squared,  # R-squared value
                }

        return models, model_reports

    def calculate_accuracy(self, df, trained_models):
        # Calculate accuracy (you can use different metrics if needed)
        total_mae = sum(mae for _, mae in trained_models.values())
        accuracy = 1 - (total_mae / len(df))
        return accuracy

    def get_label_encoders(self, df):
        label_encoders = defaultdict(LabelEncoder)

        for col in ['fabric', 'setType', 'color']:
            label_encoders[col].fit(df[col])

        return label_encoders
    

import matplotlib
matplotlib.use('agg')
class BestSellingModelTrainer(TemplateView):
    template_name = 'manage-business/train-best-selling.html'

    def get(self, request):
        return render(request, self.template_name, {'message': None, 'best_selling_dataset': None, 'raw_data': None, 'training_reports': None})

    def post(self, request):
        data = CleanTrainingSets.objects.values()
        df = pd.DataFrame(data)

        best_selling_datasets = self.calculate_quantity(df)
        cleaned_data = self.clean_data(df)
        trained_models, model_reports = self.train_model(cleaned_data)

        # Calculate training reports
        accuracy = self.calculate_accuracy(cleaned_data, trained_models)
        model_type = 'Linear Regression'  # You can set the actual model type here

        # Prepare training reports
        training_reports = {
            'accuracy': accuracy,
            'model_type': model_type,
        }

        context = {
            'message': "Success: Quantity calculated for each combination of date, location, fabric, and setType",
            'best_selling_dataset': best_selling_datasets,
            'raw_data': data,
            'trained_models': trained_models,
            'model_reports': model_reports,
            'training_reports': training_reports,
        }

        return render(request, self.template_name, context)

    def calculate_quantity(self, df):
        quantity_by_combination = []

        # Convert the 'date' column to months
        df['date'] = df['date'].apply(lambda x: x.strftime('%B'))  # Extract month name

        # Group the data by unique combinations of your desired features
        combinations = df.groupby(['date', 'location', 'fabric', 'setType'])

        for combination, data in combinations:
            total_quantity = data['qty'].sum()  # Calculate the total quantity for the combination
            quantity_by_combination.append({
                'date': combination[0],
                'location': combination[1],
                'fabric': combination[2],
                'setType': combination[3],
                'qty': total_quantity
            })

        return quantity_by_combination

    def clean_data(self, df):
        label_encoders = self.get_label_encoders(df)

        for col in ['date', 'location', 'fabric', 'setType']:
            if col in df.columns:
                df[col] = label_encoders[col].transform(df[col])
            else:
                # Handle the case when the column is not found
                print(f"Column '{col}' not found in the dataset")

        return df
    
    def train_model(self, df):
        models = {}
        model_reports = {}

        for col in ['date', 'location', 'fabric', 'setType']:
            group = df.groupby(col)
            for group_name, group_data in group:
                if len(group_data) < 2:
                    print(f"Skipping {col} group '{group_name}' due to insufficient data.")
                    continue

                X = group_data[['date', 'location', 'fabric', 'setType', 'qty', 'total_price']]
                y = group_data['qty']

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                model = LinearRegression()
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)

                group_data['predicted_qty'] = model.predict(X)

                r_squared = r2_score(y_test, y_pred)

                model_key = f'{col}_{group_name}'
                models[model_key] = (f'qty for {col} {group_name}', mae)
                
                model_reports[model_key] = {
                    'model_type': 'Linear Regression',
                    'r_squared': r_squared,
                }

        return models, model_reports

    def calculate_accuracy(self, df, trained_models):
        total_mae = sum(mae for _, mae in trained_models.values())
        accuracy = 1 - (total_mae / len(df))
        return accuracy

    def get_label_encoders(self, df):
        label_encoders = defaultdict(LabelEncoder)

        for col in ['date', 'location', 'fabric', 'setType']:
            label_encoders[col].fit(df[col])

        return label_encoders


from sklearn.tree import DecisionTreeRegressor
import matplotlib
matplotlib.use('agg')
class WinnersModelTrainer(TemplateView):
    template_name = 'manage-business/train-winners.html'

    def get(self, request):
            return render(request, self.template_name, {'message': None, 'winners_dataset': None, 'raw_data': None, 'training_reports': None})

    def post(self, request):
        data = CleanTrainingSets.objects.values()
        df = pd.DataFrame(data)

        winners_datasets = self.calculate_winners(df)
        cleaned_data = self.clean_data(df)
        linear_regression_models, linear_regression_reports = self.train_linear_regression(cleaned_data)
        decision_tree_models, decision_tree_reports = self.train_decision_tree(cleaned_data)

        # Calculate training reports
        linear_regression_accuracy = self.calculate_accuracy(cleaned_data, linear_regression_models)
        decision_tree_accuracy = self.calculate_accuracy(cleaned_data, decision_tree_models)

        context = {
            'message': "Success: Winners calculated for each combination of date, location, fabric, and setType",
            'winners_dataset': winners_datasets,
            'raw_data': data,
            'linear_regression_models': linear_regression_models,
            'linear_regression_reports': linear_regression_reports,
            'linear_regression_accuracy': linear_regression_accuracy,
            'decision_tree_models': decision_tree_models,
            'decision_tree_reports': decision_tree_reports,
            'decision_tree_accuracy': decision_tree_accuracy,
        }

        return render(request, self.template_name, context)


    def calculate_winners(self, df):
        winners_by_combination = []

        # Convert the 'date' column to months
        df['date'] = df['date'].apply(lambda x: x.strftime('%B'))  # Extract month name

        # Group the data by unique combinations of your desired features
        combinations = df.groupby(['date', 'location', 'fabric', 'setType'])

        for combination, data in combinations:
            max_qty_index = data['qty'].idxmax()  # Find the index with the highest 'qty'
            winner_product = data.loc[max_qty_index]
            winners_by_combination.append({
                'date': combination[0],
                'location': combination[1],
                'fabric': combination[2],
                'setType': combination[3],
                'winner_product': winner_product
            })

        return winners_by_combination

    def clean_data(self, df):
        label_encoders = self.get_label_encoders(df)  # Call the get_label_encoders method

        for col in ['date', 'location', 'fabric', 'setType']:
            if col in df.columns:
                df[col] = label_encoders[col].transform(df[col])
            else:
                # Handle the case when the column is not found
                print(f"Column '{col}' not found in the dataset")

        return df

    def train_linear_regression(self, df):
        models = {}
        model_reports = {}

        for col in ['date', 'location', 'fabric', 'setType']:
            group = df.groupby(col)
            for group_name, group_data in group:
                if len(group_data) < 2:
                    print(f"Skipping {col} group '{group_name}' due to insufficient data.")
                    continue

                X = group_data[['date', 'location', 'fabric', 'setType', 'qty', 'total_price']]
                y = group_data['qty']

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                model = LinearRegression()
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)

                group_data['predicted_qty'] = model.predict(X)

                r_squared = r2_score(y_test, y_pred)

                model_key = f'{col}_{group_name}'
                models[model_key] = (f'qty for {col} {group_name}', mae)
                
                model_reports[model_key] = {
                    'model_type': 'Linear Regression',
                    'r_squared': r_squared,
                }

        return models, model_reports

    def train_decision_tree(self, df):
        models = {}
        model_reports = {}

        for col in ['date', 'location', 'fabric', 'setType']:
            group = df.groupby(col)
            for group_name, group_data in group:
                if len(group_data) < 2:
                    print(f"Skipping {col} group '{group_name}' due to insufficient data.")
                    continue

                X = group_data[['date', 'location', 'fabric', 'setType', 'qty', 'total_price']]
                y = group_data['qty']

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                model = DecisionTreeRegressor()
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)

                group_data['predicted_qty'] = model.predict(X)

                r_squared = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))

                model_key = f'{col}_{group_name}'
                models[model_key] = (f'qty for {col} {group_name}', mae)

                model_reports[model_key] = {
                    'model_type': 'Decision Tree',
                    'r_squared': r_squared,
                    'rmse': rmse,
                }

        return models, model_reports

    def calculate_accuracy(self, df, trained_models):
        total_mae = sum(mae for _, mae in trained_models.values())
        accuracy = 1 - (total_mae / len(df))
        return accuracy

    def get_label_encoders(self, df):
        label_encoders = defaultdict(LabelEncoder)

        for col in ['date', 'location', 'fabric', 'setType']:
            label_encoders[col].fit(df[col])

        return label_encoders

import matplotlib
matplotlib.use('agg')
class LosersModelTrainer(TemplateView):
    template_name = 'manage-business/train-losers.html'  # Update the template name

    def get(self, request):
        return render(request, self.template_name, {'message': None, 'losers_dataset': None, 'raw_data': None, 'training_reports': None})

    def post(self, request):
        data = CleanTrainingSets.objects.values()
        df = pd.DataFrame(data)

        losers_datasets = self.calculate_losers(df)  # Update to calculate losers
        cleaned_data = self.clean_data(df)
        linear_regression_models, linear_regression_reports = self.train_linear_regression(cleaned_data)

        # Calculate training reports for losers
        linear_regression_accuracy = self.calculate_accuracy(cleaned_data, linear_regression_models)

        context = {
            'message': "Success: Losers calculated for each combination of date, location, fabric, and setType",  # Update the message
            'losers_dataset': losers_datasets,  # Update to losers_dataset
            'raw_data': data,
            'linear_regression_models': linear_regression_models,
            'linear_regression_reports': linear_regression_reports,
            'linear_regression_accuracy': linear_regression_accuracy,
        }

        return render(request, self.template_name, context)

    def calculate_losers(self, df):
        losers_by_combination = []  # Update the variable name

        # Convert the 'date' column to months
        df['date'] = df['date'].apply(lambda x: x.strftime('%B'))  # Extract month name

        # Group the data by unique combinations of your desired features
        combinations = df.groupby(['date', 'location', 'fabric', 'setType'])

        for combination, data in combinations:
            min_qty_index = data['qty'].idxmin()  # Find the index with the lowest 'qty' (losing product)
            loser_product = data.loc[min_qty_index]
            losers_by_combination.append({
                'date': combination[0],
                'location': combination[1],
                'fabric': combination[2],
                'setType': combination[3],
                'loser_product': loser_product  # Update to loser_product
            })

        return losers_by_combination

    def clean_data(self, df):
        label_encoders = self.get_label_encoders(df)  # Call the get_label_encoders method

        for col in ['date', 'location', 'fabric', 'setType']:
            if col in df.columns:
                df[col] = label_encoders[col].transform(df[col])
            else:
                # Handle the case when the column is not found
                print(f"Column '{col}' not found in the dataset")

        return df

    def train_linear_regression(self, df):
        models = {}
        model_reports = {}

        for col in ['date', 'location', 'fabric', 'setType']:
            group = df.groupby(col)
            for group_name, group_data in group:
                if len (group_data) < 2:
                    print(f"Skipping {col} group '{group_name}' due to insufficient data.")
                    continue

                X = group_data[['date', 'location', 'fabric', 'setType', 'qty', 'total_price']]
                y = group_data['qty']

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                model = LinearRegression()
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)

                group_data['predicted_qty'] = model.predict(X)

                r_squared = r2_score(y_test, y_pred)

                model_key = f'{col}_{group_name}'
                models[model_key] = (f'qty for {col} {group_name}', mae)
                
                model_reports[model_key] = {
                    'model_type': 'Linear Regression',
                    'r_squared': r_squared,
                }

        return models, model_reports

    def calculate_accuracy(self, df, trained_models):
        total_mae = sum(mae for _, mae in trained_models.values())
        accuracy = 1 - (total_mae / len(df))
        return accuracy

    def get_label_encoders(self, df):
        label_encoders = defaultdict(LabelEncoder)

        for col in ['date', 'location', 'fabric', 'setType']:
            label_encoders[col].fit(df[col])

        return label_encoders
    

    def visualize_products(request):
        # Retrieve all products
        products = Product.objects.all()

        # Extract product names
        product_names = [product.name for product in products]

        # Count the occurrences of each product name
        product_name_counts = dict(Counter(product_names))

        # Extract only the field names (attributes) of the Product model
        field_names = [field.name for field in Product._meta.get_fields()]

        return render(request, 'view/visualize-product.html', {
            'product_name_counts': product_name_counts,
            'field_names': field_names,
            'products': products,
        })

    def visualize_colors(request):
        # Retrieve all colors (assuming colors are part of the Product model)
        colors = Product.objects.values_list('color', flat=True).distinct()

        return render(request, 'view/visualize-colors.html', {
            'colors': colors,
        })

    def visualize_orders(request):
        # Retrieve all pending orders
        pending_orders = Order.objects.all()

        return render(request, 'view/visualize-pending-orders.html', {
            'pending_orders': pending_orders,
        })



import matplotlib
matplotlib.use('agg')
class CsvDataModelTrainer(TemplateView):
    template_name = 'manage-business/csv-data-view.html'

    def get(self, request):
        context = {
            'message': None,
            'models_dataset': None,
            'raw_data': None,
            'linear_regression_models': None,
            'linear_regression_reports': None,
            'linear_regression_accuracy': None,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        data = CsvData.objects.values()
        df = pd.DataFrame(data)

        # Apply one-hot encoding to categorical columns
        df = pd.get_dummies(df, columns=['Bryan House'], prefix=['Bryan House'])

        # Split the dataset into features (X) and the target (y)
        X = df.drop(columns=['quantity'])
        y = df['quantity']

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Create and train the Linear Regression model
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Make predictions on the test set
        y_pred = model.predict(X_test)

        # Calculate the Mean Absolute Error (MAE)
        mae = mean_absolute_error(y_test, y_pred)

        # Calculate the R-squared value (coefficient of determination)
        r_squared = r2_score(y_test, y_pred)

        model_product = {
            'model_type': 'Linear Regression',
            'mean_absolute_error': mae,
            'r_squared': r_squared
        }

        context = {
            'message': "Linear Regression model trained successfully.",
            'model_product': model_product,
            'raw_data': data
        }

        return render(request, self.template_name, context)

    def calculate_models(self, df):
        models_by_combination = []

        combinations = df.groupby(['fabric', 'setType'])

        for combination, data in combinations:
            model_product = self.train_linear_regression(data)
            models_by_combination.append({
                'fabric': combination[0],
                'setType': combination[1],
                'model_product': model_product
            })

        return models_by_combination

    def clean_data(self, df):
        for col in ['count', 'quantity', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(inplace=True)

        return df

    def train_linear_regression(self, df):
        X = df.drop(columns=['quantity'])
        y = df['quantity']

        dataset_size = len(df)

        if dataset_size <= 1:
            X_train, X_test, y_train, y_test = X, X, y, y
        else:
            test_size = min(0.5, max(0.1, 1 / dataset_size))
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)

        df['predicted_quantity'] = model.predict(X)

        r_squared = r2_score(y_test, y_pred)

        model_product = {
            'model_type': 'Linear Regression',
            'r_squared': r_squared,
            'mae': mae
        }

        return model_product
    


def send_low_stock_email_view(request, item_id):
    # Retrieve the inventory item
    item = Inventory.objects.get(id=item_id)
    
    # Send low stock email for the specific item
    send_low_stock_email(item)
    
    return HttpResponse("Low stock alert email sent successfully")  # A simple response to indicate success

def send_low_stock_email(item):
    subject = f"Low Stock Alert: {item}"
    message = f"The stock for {item} is running low. Current quantity: {item.quantity}. Please replenish."
    supplier_email = "clonedspot@gmail.com"  # Replace with actual supplier email
    client_email = "garneil51@gmail.com"  # Replace with actual client email

    try:
        # Send email to supplier
        send_mail(subject, message, 'development.fleekyhub@gmail.com', [supplier_email], fail_silently=False,)

        # Notify client if needed
        send_mail(subject, message, 'development.fleekyhub@gmail.com', [client_email], fail_silently=False,)

    except Exception as e:
        # Handle email sending failure gracefully
        print(f"Failed to send email: {e}")
        # Log the error or take necessary action

def inventory_view(request):
    # Fetch all Inventory items
    inventory_items = Inventory.objects.all()
    materials = Material.objects.all()
    fabric_materials = FabricMaterial.objects.all()
    products = Product.objects.all()

    low_stock_items = []

    # Check inventory levels and collect low stock items
    for item in inventory_items:
        if item.quantity <= 25:
            low_stock_items.append(item)

    # Check inventory levels for materials
    for item in materials:
        if item.qty <= 25:
            low_stock_items.append(item)

    # Check inventory levels for fabric materials
    for item in fabric_materials:
        if item.fabric_qty <= 25:
            low_stock_items.append(item)

    # Check inventory levels for products
    for item in products:
        if item.stock <= 25:
            low_stock_items.append(item)

    # If there are 10 or more low stock items, send an email
    if len(low_stock_items) >= 10:
        subject = "Low Stock Alert"
        # List all the names of the low stock items
        item_names = ", ".join([str(item) for item in low_stock_items])
        message = f"There are {len(low_stock_items)} items with a stock less than 25. The items are: {item_names}. Please replenish."
        supplier_email = "clonedspot@gmail.com"  # Replace with actual supplier email
        client_email = "garneil51@gmail.com"  # Replace with actual client email

        try:
            # Send email to supplier
            send_mail(subject, message, 'development.fleekyhub@gmail.com', [supplier_email], fail_silently=False,)

            # Notify client if needed
            send_mail(subject, message, 'development.fleekyhub@gmail.com', [client_email], fail_silently=False,)

        except Exception as e:
            # Handle email sending failure gracefully
            print(f"Failed to send email: {e}")
            # Log the error or take necessary action

    return render(request, 'view/inventory.html', {
        'inventory_items': inventory_items,
        'low_stock_items': low_stock_items,
        'materials': materials,
        'fabric_materials': fabric_materials,
        'products': products,
        # Other context data as needed
    })




def generate_possible_combinations():
    # Fetch all available materials
    raw_materials_thread = Material.objects.filter(type='Raw Materials Thread').first()
    raw_materials_packaging = Material.objects.filter(type='Raw Materials Packaging').first()
    raw_materials_attachments = Material.objects.filter(type='Raw Materials Attachments').first()

    # Fetch all fabric materials
    fabric_materials = FabricMaterial.objects.all()

    # Define required quantities for each product
    products = [
        {
            'name': 'Blockout Curtain',
            'materials': {
                'Fabric': 'Blockout',
                'Grommet': 60,
                'Rings': 8,
                'Thread': 3375
            }
        },
        {
            'name': 'Katrina Curtain',
            'materials': {
                'Fabric': 'Katrina',
                'Grommet': 60,
                'Rings': 8,
                'Thread': 2684
            }
        },
        {
            'name': 'Brocade Curtain',
            'materials': {
                'Fabric': 'Brocade',
                'Grommet': 60,
                'Rings': 8,
                'Thread': 2684
            }
        },        
        {
            'name': 'Sheer Curtain',
            'materials': {
                'Fabric': 'Sheer',
                'Grommet': 60,
                'Rings': 8,
                'Thread': 2684
            }
        },        
        
        
    ]

    available_materials = {
        'Fabric': {
            fabric.fabric: {
                'count': fabric.fabric_fcount,
                'qty': fabric.fabric_qty
            }
            for fabric in fabric_materials
        },
        'Grommet': raw_materials_packaging.count,
        'Rings': raw_materials_attachments.count,
        'Thread': raw_materials_thread.qty
    }

    possible_combinations = []

    for product_info in products:
        product_name = product_info['name']
        required_materials = product_info['materials']
        possible_combinations_for_product = []

        fabric_name = required_materials['Fabric']
        fabric_data = available_materials['Fabric'].get(fabric_name)

        # Check if the required fabric is available
        if fabric_data and fabric_data['count'] > 0 and fabric_data['qty'] > 0:
            # Check if there are enough available materials to create the product
            enough_materials = (
                available_materials['Grommet'] >= required_materials['Grommet'] and
                available_materials['Rings'] >= required_materials['Rings'] and
                available_materials['Thread'] >= required_materials['Thread']
            )

            # Generate possible combinations if enough materials are available
            if enough_materials:
                material_values = [
                    range(0, fabric_data['count'] + 1),
                    range(0, available_materials['Grommet'] // required_materials['Grommet'] + 1),
                    range(0, available_materials['Rings'] // required_materials['Rings'] + 1),
                    range(0, available_materials['Thread'] // required_materials['Thread'] + 1)
                ]

                for combination in product(*material_values):
                    combination_dict = {
                        'Product': product_name,
                        'Fabric': fabric_name,
                        'ColorCount': combination[0],
                        'Grommet': combination[1],
                        'Rings': combination[2],
                        'Thread': combination[3]
                    }
                    possible_combinations_for_product.append(combination_dict)

        possible_combinations.extend(possible_combinations_for_product)

    return possible_combinations



def curtain_ingredients_view(request):
    curtain_ingredients = CurtainIngredients.objects.all()  # Fetch all curtain ingredients
    return render(request, 'view/ingredients.html', {'curtain_ingredients': curtain_ingredients})



def add_ingredients(request):
    if request.method == 'POST':
        form = CurtainIngredientsForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            fabric = form.cleaned_data['fabric']

            # Check if the ingredient with the same name and fabric already exists
            if CurtainIngredients.objects.filter(name=name, fabric=fabric).exists():
                messages.error(request, 'Ingredient already exists!')
            else:
                curtain_ingredient = form.save(commit=False)
                custom_id = curtain_ingredient.generate_curtain_custom_id()
                curtain_ingredient.curtain_custom_id = custom_id
                curtain_ingredient.save()
                return redirect('fchub:curtain-ingredients')
    else:
        form = CurtainIngredientsForm()
    
    return render(request, 'add/add-ingredients.html', {'form': form})


def edit_ingredient(request, ingredient_id):
    ingredient = get_object_or_404(CurtainIngredients, pk=ingredient_id)

    if request.method == 'POST':
        form = CurtainIngredientsForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            return redirect('fchub:curtain-ingredients')
    else:
        form = CurtainIngredientsForm(instance=ingredient)
    
    return render(request, 'edit/edit-ingredient.html', {'form': form})


def delete_ingredient(request, ingredient_id):
    ingredient = get_object_or_404(CurtainIngredients, pk=ingredient_id)
    if request.method == 'POST':
        ingredient.delete()
        messages.success(request, 'Ingredient deleted successfully!')
        return redirect('fchub:curtain-ingredients')
    
    return render(request, 'delete/delete-ingredient.html', {'ingredient': ingredient})