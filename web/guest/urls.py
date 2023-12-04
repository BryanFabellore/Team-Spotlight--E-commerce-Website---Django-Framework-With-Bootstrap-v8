from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.static import static
app_name = "guest"
urlpatterns = [
    path('', views.index, name='index'),
    #path('guest/', views.guest, name='guest'),
    path('products/', views.products, name='products'),
    
     
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)