
from django.urls import path 
from auto import views

# define the urls
urlpatterns = [
        path('auto/', views.studies),
        path('auto/<int:pk>/', views.study_detail),
        path('auto/procdl/', views.proc_data_load),
]
