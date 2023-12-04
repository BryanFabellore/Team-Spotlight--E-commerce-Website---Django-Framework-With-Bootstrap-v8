import datetime
import random
import string
from django.db import models
from django.contrib.auth.models import User
from django.utils.dates import MONTHS
from django.db.models import Max
from datetime import datetime
from django.utils.crypto import get_random_string


class FleekyAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField('First Name', max_length=50)
    last_name = models.CharField('Last Name', max_length=50)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    custom_id = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Custom ID field
    is_customer = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Ensure is_customer is always False
        self.user.is_customer = False
        # Ensure is_superuser and is_staff are always True
        self.user.is_superuser = True
        self.user.is_staff = True

        # Generate a custom ID if it doesn't exist
        if not self.custom_id:
            self.custom_id = self.generate_custom_id()
        
        self.user.save()
        super().save(*args, **kwargs)

    def generate_custom_id(self):
        # Get the maximum ID for existing FleekyAdmin instances
        max_id = FleekyAdmin.objects.aggregate(Max('id'))['id__max']
        # Generate a unique custom ID by incrementing the max ID
        next_id = (max_id or 0) + 1
        # Convert the next ID to a string and ensure it has a consistent length
        next_id_str = str(next_id).zfill(4)
        # Other parts of the custom ID generation logic (if needed)
        username_part = self.user.username[:2].upper()
        first_name_part = self.first_name[:3].upper()
        last_name_part = self.last_name[:2].upper()

        return f"{username_part}{first_name_part}{last_name_part}{next_id_str}"

    class Meta:
        verbose_name = "Admin"


class Category(models.Model):
    FABRIC_CHOICES = (
        ('Katrina', 'Katrina'),
        ('Blockout', 'Blockout'),
        ('Sheer', 'Sheer'),
        ('Korean', 'Korean'),
    )
    
    SET_TYPE_CHOICES = (
        ('Singles', 'Singles'),
        ('3 in 1', '3 in 1'),
        ('4 in 1', '4 in 1'),
        ('5 in 1', '5 in 1'),
    )

    fabric = models.CharField(max_length=250, choices=FABRIC_CHOICES)
    setType = models.CharField(max_length=250, choices=SET_TYPE_CHOICES)
    description = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.fabric} - {self.setType}"
    
    @property
    def custom_category_id(self):
        fabric_short = self.fabric[:2]  # First two letters of fabric
        set_type_short = self.setType.replace(" ", "").replace("in", "")[:3]  # First three letters of set type
        return f"{fabric_short}{set_type_short}{self.id}"
    
class Product(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField()
    price = models.DecimalField(decimal_places=2, max_digits=10)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_image = models.ImageField(upload_to='customers/static/product_images', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=100)
    custom_id = models.CharField(max_length=20, unique=True, blank=True, null=True) 
    def __str__(self):
        return self.name
    
    #SKU
    def __str__(self):
        return self.name

    def generate_random_custom_id(self, length=10):
        # Generate a random custom ID with the first two letters of name, first three letters of color, and random characters
        characters = string.ascii_letters + string.digits
        name_prefix = self.name[:2]  # First two letters of name
        color_prefix = self.color[:3]  # First three letters of color
        random_suffix = ''.join(random.choice(characters) for _ in range(length - len(name_prefix) - len(color_prefix)))
        random_custom_id = f"{name_prefix}{color_prefix}{random_suffix}"
        return random_custom_id

    def save(self, *args, **kwargs):
        if not self.custom_id:
            # Generate and set a random custom product ID if it's not set before saving the object
            self.custom_id = self.generate_random_custom_id()
        super(Product, self).save(*args, **kwargs)




class Material(models.Model):
    Material_Choices = (
        ('Raw Materials Thread', 'Raw Materials Thread'),
        ('Raw Materials Packaging', 'Raw Materials Packaging'),
        ('Raw Materials Attachments', 'Raw Materials Attachments')
    )

    type = models.CharField(choices=Material_Choices, max_length=250)
    name = models.CharField(max_length=250)
    count = models.PositiveIntegerField(default=0)
    qty = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=250)
    description = models.CharField(max_length=250, null=True)
    Custom_material_id = models.CharField(max_length=10, unique=True, blank=True, editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()

        if not self.Custom_material_id:
            # Generate a unique ID based on type, name, and random string
            random_string = get_random_string(length=2)
            custom_material_id = f"{self.type[:4].lower()}{self.name[:4].lower()}{random_string}"
            self.Custom_material_id = custom_material_id

        super(Material, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('name', 'Custom_material_id')

class FabricMaterial(models.Model):
    FABRIC_CHOICES = (
        ('Katrina', 'Katrina'),
        ('Blockout', 'Blockout'),
        ('Sheer', 'Sheer'),
        ('Korean', 'Korean'),
        ('Brocade', 'Brocade'),
    )

    fabric_material_id = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    fabric_name = models.CharField(max_length=250)
    fabric = models.CharField(choices=FABRIC_CHOICES, max_length=250)
    color = models.CharField(max_length=100)
    
    fabric_fcount = models.PositiveIntegerField(default=0)
    fabric_qty = models.PositiveIntegerField(default=0)
    fabric_unit = models.CharField(max_length=250)
    
    fabric_description = models.CharField(max_length=250, null=True)
    def __str__(self):
        return self.fabric

    def generate_fabric_material_id(self):
        existing_fabric_materials = FabricMaterial.objects.count() + 1
        autogen_number = str(existing_fabric_materials).zfill(2)

        fabric_id = (
            self.fabric_name[:3].lower() +
            self.fabric[:3].lower() +
            self.color[:2].lower() +
            autogen_number
        )
        return fabric_id

    def save(self, *args, **kwargs):
        if not self.fabric_material_id:
            self.fabric_material_id = self.generate_fabric_material_id()

        if self.fabric_fcount is None:
            self.fabric_fcount = 0

        super(FabricMaterial, self).save(*args, **kwargs)
    
class CurtainIngredients(models.Model):
    FABRIC_CHOICES = (
        ('Katrina', 'Katrina'),
        ('Blockout', 'Blockout'),
        ('Sheer', 'Sheer'),
        ('Korean', 'Korean'),
        ('Brocade', 'Brocade'),
    )

    name = models.CharField(max_length=100)
    fabric = models.CharField(choices=FABRIC_CHOICES, max_length=250)
    fabric_count = models.PositiveIntegerField(default=0)
    fabric_unit = models.CharField(max_length=100)
    grommet_count = models.PositiveIntegerField(default=0)
    grommet_unit = models.CharField(max_length=100)
    rings_count = models.PositiveIntegerField(default=0)
    rings_unit = models.CharField(max_length=100)
    thread_count = models.PositiveIntegerField(default=0)
    thread_unit = models.CharField(max_length=100)
    length = models.PositiveIntegerField(default=0)  # Length of the curtain
    length_unit = models.CharField(max_length=100)
    curtain_custom_id = models.CharField(max_length=15, unique=True, blank=True, editable=False)

    def generate_curtain_custom_id(self):
        fabric_name = self.fabric[:4].lower() if self.fabric else ""
        name_letters = self.name[:3].lower() if self.name else ""
        incremental_numbers = str(self.pk).zfill(2)
        incremental_number = str(CurtainIngredients.objects.count() + 1).zfill(1)
        custom_id = f"{fabric_name}{name_letters}{incremental_number}"
        return custom_id

    def save(self, *args, **kwargs):
        if not self.curtain_custom_id:
            self.curtain_custom_id = self.generate_curtain_custom_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Curtain Ingredients: {self.fabric}, Grommets: {self.grommet_count}, Rings: {self.rings_count}, Thread: {self.thread_count}"


class Inventory(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True, blank=True)
    fabric_material = models.ForeignKey(FabricMaterial, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        if self.material:
            return f"Material Inventory: {self.material.name} - {self.quantity}"
        elif self.fabric_material:
            return f"Fabric Material Inventory: {self.fabric_material.fabric_name} - {self.quantity}"
        elif self.product:
            return f"Product Stock: {self.product.name} - {self.quantity}"
        return "Inventory Item"






class Tracker(models.Model):
    PAYMENT_CHOICES = (
        ('GCASH', 'GCASH'),
        ('CASH ON DELIVERY', 'CASH ON DELIVERY'),
        ('LBC', 'LBC'),
        ('OTHERS', 'OTHERS'),
    )

    PRODUCT_TAG_CHOICES = (
        (1, 'Blockout'),
        (2, '5-in-1 Katrina'),
        (3, '3-in-1 Katrina'),
        (4, 'Tieback Holder'),
    )

    FABRIC_CHOICES = (
        ('Katrina', 'Katrina'),
        ('Blockout', 'Blockout'),
        ('Sheer', 'Sheer'),
        ('None', 'None'),
    )

    SET_CHOICES = (
        ('5-in-1', '5-in-1'),
        ('3-in-1', '3-in-1'),
        ('Single', 'Single'),
        ('None', 'None'),
    )

    MONTHS = (
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    )

    fabric_type = models.CharField(max_length=250, null=True, choices=FABRIC_CHOICES)
    payment = models.CharField(max_length=250, null=True, choices=PAYMENT_CHOICES)
    price = models.PositiveIntegerField(null=True)
    color = models.CharField(max_length=250, null=True)
    product_tag = models.SmallIntegerField(choices=PRODUCT_TAG_CHOICES)
    setType = models.CharField(max_length=250, choices=SET_CHOICES, null=True)
    month_of_purchase = models.PositiveSmallIntegerField(null=True, choices=MONTHS)
    qty = models.PositiveIntegerField(null=True)
    count = models.PositiveIntegerField(null=True)

class Csv(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    csv_file = models.FileField(upload_to='fchub/admin/csv/')
    file_name = models.CharField(max_length=255)  # Add a field for storing file name

class CsvData(models.Model):
    year = models.IntegerField()
    month = models.CharField(max_length=20)
    day = models.IntegerField()
    location = models.CharField(max_length=100)
    customerName = models.CharField(max_length=100)
    fabric = models.CharField(max_length=100)
    setType = models.CharField(max_length=20)
    color = models.CharField(max_length=20)
    quantity = models.IntegerField()
    count = models.IntegerField()
    price = models.CharField(max_length=20)




 

    def __str__(self):
        return self.customerName

class SuccessfulOrder(models.Model):
    order_number = models.CharField(max_length=100)
    success_order_id = models.CharField(max_length=20, unique=True)  # Add a field for the generated ID
    date = models.DateField()
    location = models.CharField(max_length=100)
    name = models.CharField(max_length=250)
    fabric = models.CharField(max_length=250)
    setType = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    qty = models.PositiveIntegerField()
    count = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Successful Order for {self.name}"

    def generate_success_order_id(self):
        # Extract information from related Order
        order_number = self.order_number
        customer_name = self.order.customer.first_name[:3]
        username = self.order.customer.username[:3]
        location = self.location[:3]

        # Generate the success_order_id
        last_5_order_number = order_number[-5:]
        self.success_order_id = f'SuccessfulOrder-{last_5_order_number}-{customer_name}-{username}-{location}'

    def save(self, *args, **kwargs):
        if not self.success_order_id:
            self.generate_success_order_id()
        super().save(*args, **kwargs)


class TrainingSets(models.Model):
    date = models.DateField()
    location = models.CharField(max_length=100)
    fabric = models.CharField(max_length=250)
    setType = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    qty = models.PositiveIntegerField()
    count = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

class CleanTrainingSets(models.Model):
    date = models.DateField()
    location = models.CharField(max_length=100)
    fabric = models.CharField(max_length=250)
    setType = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    qty = models.PositiveIntegerField()
    count = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)


class SalesForWebData(models.Model):
    fabric_type = models.CharField(max_length=250, null=True)
    color = models.CharField(max_length=250, null=True)
    set_type = models.CharField(max_length=250, null=True)
    date = models.DateField()


class SalesForFabric(models.Model):
    date = models.DateField()
    fabric = models.CharField(max_length=250)

    
class SalesForCategory(models.Model):
    date = models.DateField()
    set_tag = models.CharField(max_length=250)


class SalesForLocation(models.Model):
    date = models.DateField()
    fabric = models.CharField(max_length=250)
    set_type = models.CharField(max_length=250)
    location = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)



class SalesForColor(models.Model):
    fabric = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    date = models.DateField()

class ToDo(models.Model):
    TASK_CHOICES = [
        ('SEW', 'Sew the curtains'),
        ('PACKAGE', 'Package the order'),
        # Add other tasks as needed
    ]

    task = models.CharField(max_length=20, choices=TASK_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=10, default='TODO')  # 'TODO', 'WORKING', 'DONE'
    comments = models.TextField(blank=True, null=True)

    # You can add more fields as needed, like related to customer/order etc.
    def __str__(self):
        return f"{self.get_task_display()} - {self.status}"