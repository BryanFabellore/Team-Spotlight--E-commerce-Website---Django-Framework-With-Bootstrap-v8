#reset
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
import requests
from .forms import CustomerEditForm, User_form, Customer_form, Address_form, UserEditForm
from .models import Cart, CartProduct, Customer, CustomerOrder, Invoice, Orders, Payment, TrackOrder
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.utils.translation import gettext as _
from .models import Customer, Product, User, Address
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.forms import formset_factory, modelformset_factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Product  # Import your Product model
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .models import Customer, Address, Product, Orders

# Create your views here.
def signup(request):
    if request.method == 'POST':
        user_form = User_form(request.POST)
        customer_form = Customer_form(request.POST)
        address_form = Address_form(request.POST)
        print(user_form)
        print(customer_form)
        print(address_form)

        if user_form.is_valid() and customer_form.is_valid() and address_form.is_valid():
            # Save the User model
            user = user_form.save()
            
            # Save the Customer model
            customer = customer_form.save(commit=False)
            customer.user = user  # Link the Customer to the User
            customer.save()

            # Save the Address model
            address = address_form.save(commit=False)
            address.customer = customer  # Link the Address to the Customer
            address.save()

            # Log in the user after successful signup
            login(request, user)
            print(customer)
            print(address)
            # Redirect to a success page or wherever you want
            return redirect('/customer/home')
    else:
        user_form = User_form()  # Use lowercase variable name here
        customer_form = Customer_form()  # Use lowercase variable name here
        address_form = Address_form()  # Use lowercase variable name here

    return render(request, 'registration/signup.html', {'user_form': user_form, 'customer_form': customer_form, 'address_form': address_form})


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'registration/login.html'
    
    def form_invalid(self, form):
        messages.error(self.request, _('Invalid username or password'))  # Add a custom error message
        return super().form_invalid(form)

def customer_logout(request):
    logout(request)
    # You can add a custom message or additional logic here if needed.
    return redirect('customer:login')  # Redirect to the login page after logout

@login_required
def customer_home_view(request):
    customer = request.user.customer
    products = Product.objects.all()
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    return render(request, 'customer/home.html', {'customer': customer, 'Products': products, 'product_count_in_cart': product_count_in_cart})

def access_denied(request):
    if isinstance(request.user, AnonymousUser):
        return render(request, 'access-denied.html')
    else:
        return redirect('customer:home')

@login_required
def profile(request):
    user_profile = request.user  # Get the user profile
    customer_profile = Customer.objects.get(user=request.user)  # Get the customer profile
    customer_addresses = Address.objects.filter(customer=customer_profile)
    return render(request, 'customer/profile.html', {
        'user_profile': user_profile,
        'customer_profile': customer_profile,
        'customer_addresses': customer_addresses,
    })

@login_required
def edit_profile(request):
    user = request.user
    customer = Customer.objects.get(user=user)

    if request.method == 'POST':
        user_form = User_form(request.POST, instance=user)
        customer_form = Customer_form(request.POST, request.FILES, instance=customer)
        address_form = Address_form(request.POST)

        if user_form.is_valid() and customer_form.is_valid() and address_form.is_valid():
            if user.email != user_form.cleaned_data['email']:
                if User.objects.filter(email=user_form.cleaned_data['email']).exists():
                    messages.error(request, 'Email already exists. Please choose a different one.')
                else:
                    user.email = user_form.cleaned_data['email']
                    user_form.save()
                    customer_form.save()
                    address_form.instance = customer
                    address_form.save()
                    messages.success(request, 'Profile updated successfully.')
                    return redirect('/customer/home')
        else:
            messages.error(request, 'There was an issue with the form submission. Please check the form fields for errors.')
    else:
        user_form = User_form(instance=user)
        customer_form = Customer_form(instance=customer)
        address_form = Address_form()

    return render(request, 'customer/edit-profile.html', {
        'user_form': user_form,
        'customer_form': customer_form,
        'address_form': address_form,
    })

@login_required
def cart_view(request):
    # Initialize cart-related variables
    product_ids = request.COOKIES.get('product_ids', '')
    product_count_in_cart = len(set(product_ids.split('|'))) if product_ids else 0
    products = None
    total = 0

    if product_ids:
        product_id_in_cart = product_ids.split('|')
        # Filter products based on IDs in the cart
        products = Product.objects.filter(id__in=product_id_in_cart)
        # Calculate the total price of items in the cart
        total = sum(p.price for p in products)

    return render(request, 'process/cart.html', {'Products': products, 'total': total, 'product_count_in_cart': product_count_in_cart})

@login_required
def add_to_cart_view(request, pk):
    # Retrieve the product
    product = Product.objects.get(id=pk)

    # Get the current product IDs in the cart from cookies
    product_ids = request.COOKIES.get('product_ids', '')

    # Split product IDs into a list
    product_id_list = product_ids.split('|') if product_ids else []

    # Check if the product is already in the cart
    if str(pk) not in product_id_list:
        product_id_list.append(str(pk))

    # Join the product IDs back into a string
    product_ids = '|'.join(product_id_list)

    # Create or update the cart by setting the product IDs as a cookie
    response = HttpResponseRedirect(reverse('customer:home'))
    response.set_cookie('product_ids', product_ids)

    # Inform the user that the product has been added to the cart
    messages.info(request, f'{product.name} added to cart successfully!')

    return response

@login_required
def remove_from_cart_view(request, pk):
    # Get the product from the database
    product = Product.objects.get(id=pk)

    # Retrieve the current product IDs in the cart from cookies
    product_ids = request.COOKIES.get('product_ids', '')

    if product_ids:
        # Split product IDs into a list
        product_id_list = product_ids.split('|')
        # Remove the selected product's ID from the list
        product_id_list.remove(str(pk))

        # Join the product IDs back into a string
        product_ids = '|'.join(product_id_list)

        # Create or update the cart by setting the modified product IDs as a cookie
        response = HttpResponseRedirect(reverse('customer:cart'))
        response.set_cookie('product_ids', product_ids)

        # Inform the user that the product has been removed from the cart
        messages.info(request, f'{product.name} removed from the cart.')

        return response

    return HttpResponseRedirect(reverse('customer:home'))
@login_required
def proceed_purchase_view(request):
    user = request.user
    customer = get_object_or_404(Customer, user=user)
    customer_address = get_object_or_404(Address, customer=customer)
    cart, created = Cart.objects.get_or_create(customer=customer)
 
    # Check if there are products in the cart
    product_ids = request.COOKIES.get('product_ids', '')
    product_id_in_cart = product_ids.split('|') if product_ids else []
    product_count_in_cart = len(set(product_id_in_cart))
    product_in_cart = product_count_in_cart > 0

    # Fetch product details from the database based on the IDs in the cookie
    products = Product.objects.filter(id__in=product_id_in_cart)

    # Calculate the total price
    total = Decimal('0')
    vat_rate = Decimal('0.12')
    for product in products:
        total += product.price

    # Calculate VAT and total with VAT
    vat = total * vat_rate
    with_vat = total + vat

    # Determine shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0
    total_price = 0

    regions_three = ["National Capital Region (NCR)", "Region I (Ilocos Region)", "Region II (Cagayan Valley)",
                     "Region III (Central Luzon)", "Region IV-A (CALABARZON)", "Region V (Bicol Region)"]
    regions_four = ["Region VI (Western Visayas)", "Region VII (Central Visayas)", "Region VIII (Eastern Visayas)"]
    regions_five = ["Region IX (Zamboanga Peninzula)", "Region X (Northern Mindanao)",
                    "Region XI (Davao Region)", "Region XII (SOCCSKSARGEN)", "Region XIII (Caraga)",
                    "Cordillera Administrative Region (CAR)", "Autonomous Region in Muslim Mindanao (ARMM)"]

    if f_region in regions_three:
        shipping_fee = Decimal('300')
        total_price = with_vat + shipping_fee
    elif f_region in regions_four:
        shipping_fee = Decimal('400')
        total_price = with_vat + shipping_fee
    elif f_region in regions_five:
        shipping_fee = Decimal('500.00')
        total_price = with_vat + shipping_fee

    # Create the order and store its ID
    customer_order = CustomerOrder.objects.create(
        customer=customer,
        email=user.email,
        address=customer_address,
        mobile_number=customer.phone_number,
        cart=cart
    )
    

    fname = f"{customer.first_name} {customer.last_name}"



    # Pass the order ID to the payment view
    return render(request, 'process/proceed-purchase.html', {
        'shipping_fee': shipping_fee,
        'total_price': total_price,
        'vat': vat,
        'with_vat': with_vat,
        'Products': products,
        'total': total,
        'user': user,
        'product_in_cart': product_in_cart,
        'product_count_in_cart': product_count_in_cart,
        'customer': customer,
        'customer_address' : customer_address,
        'customer_order': customer_order
    })

@login_required
def online_payment_view(request):
    # Your PayMongo API key (replace with your actual API key)
    api_key = "Basic c2tfdGVzdF85b3ltdlhraDhncnBwWmpHQnhYeFpjVFU6QEZsZWVreWh1Yb2tl1jkjd"

    user = User.objects.get(id=request.user.id)
    customer = get_object_or_404(Customer, user=user)
    customer_address = get_object_or_404(Address, customer=customer)
    cart = get_object_or_404(Cart, customer=customer)
    
    # Check if there are products in the cart
    product_ids = request.COOKIES.get('product_ids', '')
    product_id_in_cart = product_ids.split('|') if product_ids else []
    product_count_in_cart = len(set(product_id_in_cart))
    product_in_cart = product_count_in_cart > 0

    # Fetch product details from the database based on the IDs in the cookie
    products = Product.objects.filter(id__in=product_id_in_cart)

    # Calculate the total price and quantity based on products in the cart
    total = Decimal('0')
    quantity = 0  # Initialize quantity
    vat_rate = Decimal('0.12')  # 12% VAT rate

    for product in products:
        total += product.price
        quantity += 1  # Increment quantity for each product in the cart

    # Calculate VAT and total with VAT
    vat = total * vat_rate
    with_vat = total + vat

    # Determine shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0

    regions_three = ["National Capital Region (NCR)", "Region I (Ilocos Region)", "Region II (Cagayan Valley)",
                     "Region III (Central Luzon)", "Region IV-A (CALABARZON)", "Region V (Bicol Region)"]
    regions_four = ["Region VI (Western Visayas)", "Region VII (Central Visayas)", "Region VIII (Eastern Visayas)"]
    regions_five = ["Region IX (Zamboanga Peninzula)", "Region X (Northern Mindanao)",
                    "Region XI (Davao Region)", "Region XII (SOCCSKSARGEN)", "Region XIII (Caraga)",
                    "Cordillera Administrative Region (CAR)", "Autonomous Region in Muslim Mindanao (ARMM)"]

    if f_region in regions_three:
        shipping_fee = Decimal('300')
    elif f_region in regions_four:
        shipping_fee = Decimal('400')
    elif f_region in regions_five:
        shipping_fee = Decimal('500.00')
        
    # Prepare line items for all products in the cart
    line_items = []
    for product in products:
        line_item = {
            "currency": "PHP",
            "amount": int((product.price * Decimal('100')).to_integral_value()),  # Convert price to cents
            "description": product.description,
            "name": product.name,
            "quantity": 1  # Each product is listed separately with quantity 1
        }
        line_items.append(line_item)

    # Add a line item for the shipping fee
    shipping_line_item = {
        "currency": "PHP",
        "amount": int((shipping_fee * Decimal('100')).to_integral_value()),  # Convert shipping fee to cents
        "description": f"Shipping Fee ({f_region})",
        "name": "Shipping",
        "quantity": 1
    }

    # Add a line item for the VAT
    vat_line_item = {
        "currency": "PHP",
        "amount": int((vat * Decimal('100')).to_integral_value()),  # Convert VAT to cents
        "description": "VAT (12%)",
        "name": "VAT",
        "quantity": 1
    }

    line_items.append(shipping_line_item)
    line_items.append(vat_line_item)

    fname = f"{customer.first_name} {customer.last_name}"

    # Prepare the payload for PayMongo API
    payload = {
        "data": {
            "attributes": {
                "billing": {
                    "address": {
                        "city": customer_address.city,
                        "state": customer_address.region,
                        "postal_code": customer_address.zipcode,
                        "country": "PH",  # Philippines (ISO 3166-1 alpha-2 code)
                        "line1": customer_address.barangay
                    },
                    "name": fname,
                    "email": user.email,
                    "phone": customer.phone_number
                },
                "send_email_receipt": False,  # Set to False
                "show_description": True,
                "show_line_items": True,
                "cancel_url": "http://127.0.0.1:5000/customer/proceed-purchase/",  # Add cancel URL
                "success_url": "http://127.0.0.1:5000/customer/home",  # Add Success URL
                "description": "Order Description",
                "line_items": line_items,
                "payment_method_types": ["gcash", "grab_pay", "paymaya"]  # Add payment method types
            }
        }
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": api_key
    }

    # API endpoint for payment creation
    url = "https://api.paymongo.com/v1/checkout_sessions"
    try:
        # Make a POST request to create the payment session
        response = requests.post(url, json=payload, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Payment session created successfully, retrieve the session URL
            payment_session_data = response.json()
            checkout_url = payment_session_data.get("data", {}).get("attributes", {}).get("checkout_url")

            # Redirect the user to the checkout URL
            return HttpResponseRedirect(checkout_url)
        else:
            # Payment session creation failed
            error_message = response.json().get("errors", "Payment session creation failed")
            # Handle the error as needed, e.g., return an error response
            return JsonResponse({"error": error_message}, status=400)
    except requests.exceptions.RequestException as e:
        # Handle network or request-related errors
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)