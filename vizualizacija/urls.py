from django.urls import path
from . import views

urlpatterns = [ 
       path('', views.home , name="index"),
       path('saobracaj/', views.saobracaj , name="saobracaj"),
       path('skole/', views.skole , name="skole"),
]
 