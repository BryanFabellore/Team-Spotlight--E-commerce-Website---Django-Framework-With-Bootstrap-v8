from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from fchub.models import Product
from django.db.models import Max

class Customer(models.Model):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, verbose_name='First Name')
    last_name = models.CharField(max_length=50, verbose_name='Last Name')
    email = models.EmailField()
    phone_number = models.CharField(max_length=30)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_addresses')
    profile_pic = models.ImageField(
        upload_to='customers/static/customer_profile_pic',
        null=True,
        default='customers/profile_pic/customer_profile_pic/akbay.png'
    )
    custom_id = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Increased max_length
    is_customer = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.custom_id:
            self.custom_id = self.generate_custom_id()
        
        if not self.user.is_staff and not self.user.is_superuser:
            self.user.is_customer = True
            self.user.save()
        
        super().save(*args, **kwargs)

    def generate_custom_id(self):
        # Get the maximum ID for existing customers
        max_id = Customer.objects.aggregate(Max('id'))['id__max']
        
        # Generate a unique custom ID by incrementing the max ID
        next_id = (max_id or 0) + 1

        # Convert the next ID to a string and ensure it has a consistent length
        next_id_str = str(next_id).zfill(4)

        # Other parts of the custom ID generation as before
        username_part = self.user.username[:2].upper()
        first_name_part = self.first_name[:3].upper()
        last_name_part = self.last_name[:2].upper()
        gender_part = self.gender[:1].upper()

        return f"{username_part}{first_name_part}{last_name_part}{gender_part}{next_id_str}"

    class Meta:
        verbose_name = "Customer"


class Address(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='address_customers')
    region = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    detailed_address = models.CharField(max_length=250)
    zipcode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.detailed_address}, {self.barangay}, {self.city}, {self.province}, {self.region}, {self.zipcode}"

    class Meta:
        verbose_name = "Address"

class CartManager(models.Manager):
    def get_or_create_cart(self, customer):
        cart, created = self.get_or_create(customer=customer)
        return cart, created

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    total_quantity = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    objects = CartManager()  

    def __str__(self):
        return self.customer.user.username + "'s Cart"

    def update_totals(self):
        total_price = 0
        total_quantity = 0

        for cart_item in self.cartitem_set.all():
            cart_item.calculate_item_total()  # Calculate item total for each cart item
            total_price += cart_item.item_total
            total_quantity += cart_item.quantity

        self.total_price = total_price
        self.total_quantity = total_quantity
        self.save()

    def add_to_cart(self, product):
        # Check if the product is already in the cart
        cart_item, created = CartItem.objects.get_or_create(cart=self, product=product)
        
        # If the item was created, set its quantity to 1, else, increment the quantity
        if created:
            cart_item.quantity = 1
        else:
            cart_item.quantity += 1
        
        cart_item.save()
        self.update_totals()

    def calculate_totals(self):
        total_price = 0
        total_quantity = 0

        for cart_item in self.cartitem_set.all():
            cart_item.calculate_item_total()  # Calculate item total for each cart item
            total_price += cart_item.item_total
            total_quantity += cart_item.quantity

        return total_price, total_quantity

    def remove_from_cart(self, product):
        try:
            cart_item = self.cartitem_set.get(product=product)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
            self.update_totals()
        except CartItem.DoesNotExist:
            pass  # Handle the case where the product is not in the cart
        
    def clear_cart(self):
        # Remove all cart items associated with this cart
        self.cartitem_set.all().delete()
        # Reset total_quantity and total_price to zero
        self.total_quantity = 0
        self.total_price = 0
        self.save()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_item_total(self):
        self.item_total = self.quantity * self.product.price
        self.save()

    class Meta:
        unique_together = ['cart', 'product']

    @classmethod
    def update_cart_quantity(cls, cart, product, quantity):
        cart_item, created = cls.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity = quantity
        cart_item.save()

        cart.update_totals()



class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    )

    PAYMENT_CHOICES = (
        ("Online", "Online"),
        ("COD", "COD"),
    )

    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES)
    total_price = models.DecimalField(max_digits=30, decimal_places=2)
    order_number = models.CharField(max_length=15, unique=True)
    products = models.ManyToManyField(Product)

    def __str__(self):
        return self.order_number
    
    def generate_order_number(self):
        if not self.order_number:
            order_date = self.order_date.strftime('%Y%m%d')
            random_string = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
            first_letter_payment = self.payment_method[0].upper()
            self.order_number = f'{order_date}-{first_letter_payment}{self.customer.id}-{random_string}'

    def save(self, *args, **kwargs):
        self.generate_order_number()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.calculate_item_total()  # Calculate item total before saving
        super().save(*args, **kwargs)

    def calculate_item_total(self):
        self.item_total = self.quantity * self.product.price

    def __str__(self):
        return f"{self.product.name} in Order {self.order.order_number}"



class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order {self.order.order_number}"
    