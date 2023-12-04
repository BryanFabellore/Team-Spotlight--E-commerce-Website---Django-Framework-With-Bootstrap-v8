from collections import defaultdict
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from matplotlib import category
import requests
from xhtml2pdf import pisa
from fchub.models import Category, FleekyAdmin
from .forms import CustomerEditForm, CustomerProfileForm, SignupForm, AddressEditForm ,CartForm, CartItemForm, OrderForm, PaymentForm, UserEditForm
from .models import Cart, CartItem, Customer, Order, OrderItem,  Payment
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
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Product  # Import your Product model
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .models import Customer, Address, Product
from django.contrib.auth.models import User
from datetime import datetime  # Import datetime module
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate, login
import io
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.views.generic import View
from .models import Order
from django.template.loader import get_template


# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Create the user
            user = form.save()

            # Retrieve address components
            region = form.cleaned_data['region']
            province = form.cleaned_data['province']
            city = form.cleaned_data['city']
            barangay = form.cleaned_data['barangay']
            street = form.cleaned_data['street']
            detailed_address = form.cleaned_data.get('detailed_address', '')  # Provide a default value if not present
            zipcode = form.cleaned_data.get('zipcode', '')  # Provide a default value if not present

            # Create the Customer object
            customer = Customer(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number'],
                gender=form.cleaned_data['gender'],
                profile_pic=form.cleaned_data.get('profile_pic', None)
            )
            customer.save()

            # Create the Address object
            address, created = Address.objects.get_or_create(
                region=region,
                province=province,
                city=city,
                barangay=barangay,
                street=street,
                detailed_address=detailed_address,
                zipcode=zipcode,
                customer=customer  # Associate the Address with the Customer instance
            )
            address.save()

            login(request, user)  # Log the user in after registration
            return redirect('/customer/home')  # Redirect to your desired page after successful registration
    else:
        form = SignupForm()

    return render(request, 'registration/signup.html', {'form': form})


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(self.request, user)

            if is_customer(user):
                return redirect('customer:home')
            elif user.is_staff:  # Check if user is an admin (staff)
                return redirect('fchub:dashboard')
            else:
                return redirect('customer:home')  # Redirect to login page if not an admin or customer

        else:
            return super().form_invalid(form)

    
def customer_logout(request):
    logout(request)
    cache.clear()  # Clear the cache for all users
    return redirect('customer:login')  # Redirect to the login page after logout

@login_required
def customer_home_view(request):
    customer = request.user.customer
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
    return render(request, 'customer/home.html', {'customer':customer,'products': products, 'FABRIC_CHOICES': fabric_choices, 'SET_TYPE_CHOICES': set_type_choices})



def access_denied(request):
    if isinstance(request.user, AnonymousUser):
        return render(request, 'access-denied.html')
    else:
        return redirect('customer:home')

@login_required
def profile(request):
    # Get the user's customer profile
    customer_profile = Customer.objects.get(user=request.user)
    
    # Get addresses associated with the customer
    customer_addresses = Address.objects.filter(customer=customer_profile)
    
    # Assuming you have a way to retrieve orders for the customer, replace this line with your logic
    # orders = Order.objects.filter(customer=customer_profile)

    return render(request, 'customer/profile.html', {
        'customer_profile': customer_profile,
        'customer_addresses': customer_addresses,
        # 'orders': orders,
    })

@login_required
def edit_profile(request):
    customer = request.user.customer
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer:profile')
    else:
        form = CustomerProfileForm(instance=customer)
    
    context = {'form': form}
    return render(request, 'customer/edit-profile.html', context)

# Cart Management Views
@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create_cart(customer=request.user.customer)
    cart_items = cart.cartitem_set.all()  # Access the Cart object in the tuple
    total_price, total_quantity = cart.calculate_totals()

    return render(request, 'process/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_quantity': total_quantity,
        'cart': cart,
    })
from django.views.decorators.http import require_POST

@login_required
def update_quantity_view(request, product_id):
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 0))
        cart_item = get_object_or_404(CartItem, product_id=product_id, cart__customer=request.user.customer)

        if new_quantity >= 1:
            cart_item.quantity = new_quantity
            cart_item.save()
        # Redirect back to the cart view after updating the quantity
        return redirect('customer:cart')
    # Handle other cases or errors if necessary
    return redirect('customer:cart')






@login_required
def add_to_cart_view(request, pk):
    product = Product.objects.get(pk=pk)
    customer = request.user.customer
    cart, created = Cart.objects.get_or_create_cart(customer)
    cart.add_to_cart(product)

    print(f'{product.name} added to the cart successfully!')  # Print to your server console
    messages.info(request, f'{product.name} added to the cart successfully!')

    return HttpResponseRedirect(reverse('customer:home'))

@login_required
def remove_from_cart_view(request, pk):
    product = Product.objects.get(pk=pk)
    customer = request.user.customer
    cart, _ = Cart.objects.get_or_create_cart(customer)

    try:
        cart_item = cart.cartitem_set.get(product=product)
        cart_item.delete()  # Remove the cart item for the specific product
        messages.info(request, f'{product.name} removed from the cart successfully!')
    except CartItem.DoesNotExist:
        messages.info(request, f'{product.name} is not in the cart.')

    return redirect('customer:cart')

@login_required
def clear_cart_view(request):
    cart, created = Cart.objects.get_or_create_cart(customer=request.user.customer)
    cart.clear_cart()
    return HttpResponseRedirect(reverse('customer:cart'))


@login_required
def delete_from_cart_view(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk)

    # Check if the cart item belongs to the current user
    if cart_item.cart.customer.user != request.user:
        return redirect('customer:cart')  # Redirect back to the cart page

    cart_item.delete()
    return redirect('customer:cart')  # Redirect back to the cart page

@login_required
def increase_quantity_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    customer = request.user.customer
    cart, created = Cart.objects.get_or_create_cart(customer)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    cart_item.quantity += 1
    cart_item.save()
    cart.update_totals()
    return HttpResponseRedirect(reverse('customer:cart'))

@login_required
def decrease_quantity_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    customer = request.user.customer
    cart, created = Cart.objects.get_or_create_cart(customer)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        cart.update_totals()

    else:
        # If quantity is 1, remove the item from the cart
        cart_item.delete()


    return HttpResponseRedirect(reverse('customer:cart'))


@login_required
def proceed_purchase_view(request):
    user = request.user
    customer = get_object_or_404(Customer, user=user)
    customer_address = get_object_or_404(Address, customer=customer)

    # Retrieve the user's cart, ensuring it's not a tuple
    cart, created = Cart.objects.get_or_create_cart(customer=customer)

    if created:
        # If the cart was created in this request, you might want to handle it accordingly
        pass

    cart_items = cart.cartitem_set.all()

    total = cart.total_price
    quantity = cart.total_quantity

    # Calculate VAT and total with VAT
    vat_rate = Decimal('0.12')
    vat = total * vat_rate
    with_vat = total + vat
    
    # Determine the shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0
    total_price = 0

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
    total_price = with_vat + shipping_fee

    return render(request, 'process/proceed-purchase.html', {
        'shipping_fee': shipping_fee,
        'total_price': total_price,
        'vat': vat,
        'with_vat': with_vat,
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
        'user': user,
        'customer': customer,
        'customer_address': customer_address,
        'vat_rate': vat_rate,
    })

@login_required
def confirmation_cod_payment(request):
    user = request.user
    customer = get_object_or_404(Customer, user=user)
    customer_address = get_object_or_404(Address, customer=customer)

    # Retrieve the user's cart, ensuring it's not a tuple
    cart, created = Cart.objects.get_or_create_cart(customer=customer)

    if created:
        # If the cart was created in this request, you might want to handle it accordingly
        pass

    # Assuming that you are using the correct attribute name "cartitem_set"
    cart_items = cart.cartitem_set.all()

    total = cart.total_price
    quantity = cart.total_quantity

    # Calculate VAT and total with VAT
    vat_rate = Decimal('0.12')
    vat = total * vat_rate
    with_vat = total + vat

    # Determine the shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0
    total_price = 0

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

    total_price = with_vat + shipping_fee

    return render(request, 'process/confirmation-cod-payment.html', {
        'shipping_fee': shipping_fee,
        'total_price': total_price,
        'vat': vat,
        'with_vat': with_vat,
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
        'user': user,
        'customer': customer,
        'customer_address': customer_address,
        'vat_rate': vat_rate,
    })

@login_required
def success_cod_payment_view(request):
    user = request.user
    customer = get_object_or_404(Customer, user=user)
    customer_address = get_object_or_404(Address, customer=customer)

    # Retrieve the user's cart, ensuring it's not a tuple
    cart, created = Cart.objects.get_or_create_cart(customer=customer)

    if created:
        # If the cart was created in this request, you might want to handle it accordingly
        pass

    # Assuming that you are using the correct attribute name "cartitem_set"
    cart_items = cart.cartitem_set.all()

    total = cart.total_price
    quantity = cart.total_quantity

    # Calculate VAT and total with VAT
    vat_rate = Decimal('0.12')
    vat = total * vat_rate
    with_vat = total + vat

    # Determine the shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0
    total_price = 0

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
        shipping_fee = Decimal('500.00')

    total_price = with_vat + shipping_fee

    # Create an order
    order = Order.objects.create(
        status="Pending",
        customer=customer.user,  # Assuming "user" is the User instance
        shipping_address=customer_address,
        payment_method="Cash on Delivery (COD)",
        total_price=total_price,
        order_date=timezone.now(),
    )

    # Create order items based on cart items
    order_items = []
    for cart_item in cart_items:
        order_item = OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            item_total=cart_item.quantity * cart_item.product.price,
        )
        order_items.append(order_item)

    # Clear the cart
    cart.clear_cart()

    return render(request, 'process/success-cod-payment.html', {'order': order, 'order_items': order_items})



# Updated online_payment_view
@login_required
def online_payment_view(request):
    # Your PayMongo API key (replace with your actual API key)
    api_key = "Basic c2tfdGVzdF85b3ltdlhraDhncnBwWmpHQnhYeFpjVFU6"

    user = request.user
    customer = get_object_or_404(Customer, user=user)
    customer_address = get_object_or_404(Address, customer=customer)

    # Retrieve the user's cart using the Cart model
    cart, created = Cart.objects.get_or_create_cart(customer=customer)
    cart_items = cart.cartitem_set.all()

    total = cart.total_price
    quantity = cart.total_quantity

    # Calculate VAT and total with VAT
    vat_rate = Decimal('0.12')
    vat = total * vat_rate
    with_vat = total + vat

    # Determine shipping fee based on the region
    f_region = customer_address.region
    shipping_fee = 0
    total_price = 0

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
        shipping_fee = Decimal('500.00')

    total_price = with_vat + shipping_fee

    # Prepare line items for all products in the cart
    line_items = []
    for cart_item in cart_items:
        product = cart_item.product
        line_item = {
            "currency": "PHP",
            "amount": int((product.price * Decimal('100')).to_integral_value()),  # Convert price to cents
            "description": product.description,
            "name": product.name,
            "quantity": cart_item.quantity
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
                    "email": customer.email,  # Use the email from the customer
                    "phone": customer.phone_number
                },
                "send_email_receipt": False,  # Set to False
                "show_description": True,
                "show_line_items": True,
                "cancel_url": request.build_absolute_uri(reverse('customer:proceed-purchase')),  # Cancel URL
                "success_url":request.build_absolute_uri(reverse('customer:home')),  # Success URL
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
            response = HttpResponseRedirect(checkout_url)

            order = Order.objects.create(
                status="Pending",
                customer=customer.user,  # Use the related User instance, assuming "user" is the correct attribute
                shipping_address=customer_address,
                payment_method="Online Payment",
                total_price=total_price,
                order_date=timezone.now(),
            )


            # Create OrderProduct instances for each product in the cart
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    item_total=cart_item.quantity * cart_item.product.price,
                )

            # Clear the cart after a successful payment
            cart_items.delete()

            return response  # Redirect the user to the checkout URL

        else:
            # Payment session creation failed
            error_message = response.json().get("errors", "Payment session creation failed")
            # Handle the error as needed, e.g., return an error response
            return JsonResponse({"error": error_message}, status=400)

    except requests.exceptions.RequestException as e:
        # Handle network or request-related errors
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)





@login_required
def my_order_view(request):
    user = request.user
    orders = Order.objects.filter(customer=user).order_by('-order_date')


    # Render a template and pass the orders as context
    return render(request, 'customer/my-order.html', {'orders': orders})


def render_to_pdf(template_path, context_dict):
    template = get_template(template_path)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def generate_invoice(request, order_id):
    # Fetch the order with the given order_id
    order = Order.objects.get(id=order_id)

    # Retrieve related customer, address, and order items
    customer = order.customer
    shipping_address = order.shipping_address
    order_items = order.order_items.all()

    # Calculate the total price for the order
    total_price = sum(item.item_total for item in order_items)

    # Access the user-related fields from the customer's profile
    customer_profile = Customer.objects.get(user=request.user)
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
    pdf = render_to_pdf('process/download-invoice.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="invoice.pdf"'
        return response

    return HttpResponse("Error rendering PDF", status=500)


