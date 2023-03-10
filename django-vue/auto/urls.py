
from django.urls import path 
from auto import views

# define the urls
urlpatterns = [
        path('auto/', views.studies),
        path('auto/<int:pk>/', views.study_detail),
        path('auto/procdl/', views.proc_data_load),
        path('auto/proccal/', views.proc_cal),
        path('auto/procacq/', views.proc_acq),
        path('auto/get_cohort_list/', views.get_cohort_list)

]
