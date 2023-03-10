
from django.urls import path 
from auto import views

# define the urls
urlpatterns = [
        path('auto/', views.studies),
        path('auto/<int:pk>/', views.study_detail),
        path('auto/procdl/', views.proc_data_load),
        path('auto/proccal/', views.proc_cal),
        path('auto/procacq/', views.proc_acq),
        path('auto/get_cohort_list/', views.get_cohort_list),
        path('auto/put_new_cohort/', views.put_new_cohort),
        path('auto/get_mouse_list/', views.get_mouse_list),
        path('auto/put_mouse_list/', views.put_mouse_list)

]
