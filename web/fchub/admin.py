from django.contrib import admin
from .models import FleekyAdmin, Material, Category, Product, Tracker, Csv, CsvData

# Register the models in the admin site
admin.site.register(FleekyAdmin)
admin.site.register(Material)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Tracker)
admin.site.register(Csv)
admin.site.register(CsvData)
