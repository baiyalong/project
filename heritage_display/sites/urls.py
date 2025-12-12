from django.urls import path
from . import views

app_name = 'sites'

urlpatterns = [
    path('', views.site_list, name='list'),
    path('<int:pk>/', views.site_detail, name='detail'),
]
