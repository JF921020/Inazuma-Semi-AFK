from django.urls import path
from . import views

app_name = 'windowselector'

urlpatterns = [
    path('', views.window_selector, name='window_selector'),
]