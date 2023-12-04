from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
app_name = 'fchub'
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.fchub_logout, name='logout'),

    path('customers/', views.view_customer, name='customers'),

    path('orders/', views.view_order, name='orders'),
    path('update-status/<int:order_id>/', views.update_status, name='update-status'),
    path('generate-invoice/<int:order_id>/', views.generate_invoice, name='generate-invoice'),
    path('full-details/<int:order_id>/', views.view_full_details, name='full-details'),


    path('category/', views.category_list, name='category'),
    path('category/add', views.add_category, name='add-category'),
    path('category/edit/<int:category_id>/', views.edit_category, name='edit-category'),
    path('category/delete/<int:category_id>/', views.delete_category, name='delete-category'),
    

    path('products/', views.view_product, name='products'),
    path('products/add-products/', views.add_product, name='add-products'),
    path('products/delete-product/<int:pk>', views.delete_product,name='delete-product'),
    path('edit-product/<int:pk>/', views.edit_product, name='edit-product'),
    
    path('materials/', views.view_materials, name='materials'),
    path('materials/edit-regular-material/<int:material_id>/', views.edit_regular_material, name='edit-regular-material'),
    path('materials/delete-regular-material/<int:pk>/', views.delete_regular_material, name='delete-regular-material'),
    
    path('materials/edit-fabric-material/<int:material_id>/', views.edit_fabric_material, name='edit-fabric-material'),
    path('materials/delete-fabric-material/<int:pk>/', views.delete_fabric_material, name='delete-fabric-material'),

    path('materials/choose-material/', views.choose_material_type, name='choose-material'),
    path('materials/add-regular-material/', views.add_regular_material, name='add-regular-material'),
    path('materials/add-fabric-material/', views.add_fabric_material, name='add-fabric-material'),
    
    path('track-purchase/', views.view_purchase, name='track-purchase'), 
    path('track-purchase/add-purchase/', views.add_purchase, name='add-purchase'),
    path('track-purchase/edit-purchase/<int:purchase_id>/', views.edit_purchase, name='edit-purchase'),
    path('track-purchase/delete-purchase/<int:purchase_id>/', views.delete_purchase, name='delete-purchase'),
    
    
    path('manage-business/', views.view_manage_business, name='manage-business'),
    
    path('manage-business/users-admins', views.users_admins, name='users-admins'),
    path('users/', views.users_admins, name='users-admins'),
    path('list-admins/add-admin/', views.add_admin, name='add-admin'),
    path('list-admins/delete-admin/<int:pk>/', views.delete_admin, name='delete-admin'),

    path('upload-csv', views.upload_csv, name='upload-csv'),
    path('delete-csv/', views.delete_csv, name='delete-csv'),
    path('migrate-csv/<int:csv_id>/', views.migrate_csv, name='migrate-csv'),
    path('get-csv-data/<int:file_id>/', views.get_csv_data, name='get-csv-data'),

    path('successful-orders/', views.successful_orders, name='successful-orders'),
    path('download-successful-orders-csv/', views.download_successful_orders_csv, name='download-successful-orders-csv'),

    path('fchub-data-model', views.view_fchub_model, name='fchub-data-model'),
    path('fchub/migrate-fchub-data/', views.migrate_fchub_data, name='migrate-fchub-data'),
    path('fchub/migrate-fchub-data/', views.migrate_fchub_data, name='migrate-fchub-data'),
    path('delete-all-data/', views.delete_all_data, name='delete-all-data'),
    path('delete-fabric-data/', views.delete_fabrics_data, name='delete-fabric-data'),
    path('delete-setType-data/', views.delete_setType_data, name='delete-setType-data'),
    path('delete-color-data/', views.delete_color_data, name='delete-color-data'),
    path('delete-location-data/', views.delete_location_data, name='delete-location-data'),
    path('delete-clean-all-data/', views.delete_clean_all_data, name='delete-clean-all-data'),





    path('fchub/migrate-fabric-data/', views.migrate_fabric_data, name='migrate-fabric-data'),
    path('migrate-category-data/', views.migrate_category_data, name='migrate-category-data'),
    path('migrate-location-data/', views.migrate_location_data, name='migrate-location-data'),
    path('migrate-color-data/', views.migrate_color_data, name='migrate-color-data'),
    path('migrate-training-data/', views.migrate_training_data, name='migrate-training-data'),

    path('sales/', views.sales_for_fabric_list, name='sales-for-fabric-list'),
    path('sales-for-category/', views.SalesForCategoryView.as_view(), name='sales-for-category-list'),
    
    path('sales-for-location/', views.sales_for_location_list, name='sales-for-location'),
    path('sales-for-color/', views.SalesForColorView.as_view(), name='sales-for-color-list'),


   path('train-top-selling/', views.TopSellingModelTrainer.as_view(), name='train-top-selling'),
   path('train-best-selling/', views.BestSellingModelTrainer.as_view(), name='train-best-selling'),
   path('train-winners/', views.WinnersModelTrainer.as_view(), name='train-winners'),
   #path('train-losers/', views.LosersModelTrainer.as_view(), name='train-losers'),

   #path('visualize-products/', views.visualize_products, name='visualize-products'),
   #path('visualize-colors/', views.visualize_products, name='visualize-colors'),
   #path('visualize-orders/', views.visualize_products, name='visualize-orders'),

   path('view-csv-data', views.CsvDataModelTrainer.as_view(), name='csv-data-view'),
   
   path('inventory/', views.inventory_view, name='inventory'),

   path('curtain-ingredients/', views.curtain_ingredients_view, name='curtain-ingredients'), 
   path('curtain-ingredients/add-ingredients', views.add_ingredients, name='add-ingredients'), 
   path('curtain-ingredients/edit-ingredient/<int:ingredient_id>/', views.edit_ingredient, name='edit-ingredient'),
   path('curtain-ingredients/delete-ingredient/<int:ingredient_id>/', views.delete_ingredient, name='delete-ingredient'),
   
   path('send-low-stock-email/<int:item_id>/', views.send_low_stock_email_view, name='send_low_stock_email_view'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
