from rest_framework import routers
from auto.viewsets import DataViewSet
from django.views.decorators.csrf import csrf_exempt

router = routers.DefaultRouter()
router.register(r'files', DataViewSet, basename='data')

