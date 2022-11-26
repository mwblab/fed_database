from rest_framework import routers,serializers,viewsets
from .models import Study

class TaskSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Study
        fields = ['id', 'studyDisplayName', 'studyDesc', 'startDate', 'endDate'] 
