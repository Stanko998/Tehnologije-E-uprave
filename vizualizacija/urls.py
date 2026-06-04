from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="index"),
    path("saobracaj/", views.saobracaj, name="saobracaj"),
    path("api/saobracaj/", views.saobracajApi, name="saobracaj_api"),
    path("skole/", views.skole, name="skole"),
    path("api/skole/", views.skoleApi, name="skole_api"),
]
