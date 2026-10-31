from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('process/', views.process_pdf, name='process_pdf'),

    path('history/', views.history, name='history'),
]