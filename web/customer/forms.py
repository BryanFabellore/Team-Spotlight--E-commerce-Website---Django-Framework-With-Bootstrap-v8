from django import forms
from django.contrib.auth.models import User
from .models import Customer, Address, Product, Cart,  Payment, CartItem, Order
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext as _
from django.contrib.auth.forms import UserChangeForm


class SignupForm(UserCreationForm):

    email = forms.EmailField(max_length=200, help_text='Required. Enter a valid email address', required=True)
    phone_number = forms.CharField(max_length=30, required=True)
    gender = forms.ChoiceField(choices=Customer.GENDER_CHOICES, required=True)
    
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)

    # Address fields
    region = forms.CharField(max_length=100, required=True)
    province = forms.CharField(max_length=100, required=True)
    city = forms.CharField(max_length=100, required=True)
    barangay = forms.CharField(max_length=100, required=True)
    street = forms.CharField(max_length=100, required=True)
    detailed_address = forms.CharField(max_length=250, required=False)
    zipcode = forms.CharField(max_length=10, required=False)
    profile_pic = forms.ImageField()
    class Meta:
        model = Customer
        fields = ( 'email','phone_number', 'gender', 'first_name', 'last_name', 'region', 'province', 'city', 'barangay', 'street', 'detailed_address', 'zipcode', 'profile_pic')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set a default value for profile_pic
        self.fields['profile_pic'].initial = '/fchub/customers/customer_pic/akbay.png'

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2',)

    def clean(self):
            cleaned_data = super().clean()
            password1 = cleaned_data.get('password1')
            password2 = cleaned_data.get('password2')

            if password1 and password2 and password1 != password2:
                raise forms.ValidationError("Passwords do not match. Please enter matching passwords.")

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'gender', 'profile_pic']
    
    region = forms.CharField(max_length=100, required=False)
    province = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=False)
    barangay = forms.CharField(max_length=100, required=False)
    street = forms.CharField(max_length=100, required=False)
    detailed_address = forms.CharField(max_length=250, required=False)
    zipcode = forms.CharField(max_length=10, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.address:
            address = self.instance.address
            self.fields['region'].initial = address.region
            self.fields['province'].initial = address.province
            self.fields['city'].initial = address.city
            self.fields['barangay'].initial = address.barangay
            self.fields['street'].initial = address.street
            self.fields['detailed_address'].initial = address.detailed_address
            self.fields['zipcode'].initial = address.zipcode

    def save(self, commit=True):
        customer = super().save(commit=False)
        address, created = Address.objects.get_or_create(customer=customer)
        address.region = self.cleaned_data['region']
        address.province = self.cleaned_data['province']
        address.city = self.cleaned_data['city']
        address.barangay = self.cleaned_data['barangay']
        address.street = self.cleaned_data['street']
        address.detailed_address = self.cleaned_data['detailed_address']
        address.zipcode = self.cleaned_data['zipcode']
        if commit:
            address.save()
            customer.save()
        return customer

class UserEditForm(UserChangeForm):
    class Meta:
        model = User  # Set the model to User
        fields = ('username',)
class CustomerEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'gender')
class AddressEditForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('region', 'province', 'city', 'barangay', 'street', 'detailed_address', 'zipcode')

class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['customer']

    def __init__(self, *args, **kwargs):
        super(CartForm, self).__init__(*args, **kwargs)
        # Customize the customer field if needed

        self.fields['customer'].widget = forms.Select(attrs={
            'class': 'form-control'
        })

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['cart', 'product', 'quantity']

    def __init__(self, *args, **kwargs):
        super(CartItemForm, self).__init__(*args, **kwargs)
        # Customize the cart, product, and quantity fields if needed

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address', 'payment_method']

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        # Customize the fields if needed

    def save(self, commit=True):
        order = super(OrderForm, self).save(commit=False)
        order.customer = self.initial['customer']  # Set the customer based on the initial data
        order.total_price = self.initial['total_price']  # Set the total price based on the initial data

        if commit:
            order.save()
        return order
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        exclude = ('payment_date',)
        fields = ['order', 'amount', 'payment_method']

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        # Customize the fields if needed