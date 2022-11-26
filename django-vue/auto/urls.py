
from django.urls import path 
from auto import views

# define the urls
urlpatterns = [
        path('auto/', views.studies),
]
