
from rest_framework import viewsets
from .models import Data
from .serializers import DataSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class DataViewSet(viewsets.ModelViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer
