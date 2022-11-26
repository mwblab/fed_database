from django.shortcuts import render

# Create your views here.

# parsing data from the client
from rest_framework.parsers import JSONParser
# To bypass having a CSRF token
from django.views.decorators.csrf import csrf_exempt
# for sending response to the client
from django.http import HttpResponse, JsonResponse
# API definition for task
from .serializers import TaskSerializer
from .models import Study


@csrf_exempt
def studies(request):

    if(request.method == 'GET'):
        studies = Study.objects.all()
        serializer = TaskSerializer(studies, many=True)
        return JsonResponse(serializer.data,safe=False)
    elif(request.method == 'POST'):
        print("in backend post")
        data = JSONParser().parse(request)
        print(request)
        print(data)
        serializer = TaskSerializer(data=data)
        if(serializer.is_valid()):
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        else:
            print("data not valid")
        
    return JsonResponse(serializer.errors, status=400)


@csrf_exempt
def study_detail(request, pk):
    try:
        study = Study.objects.get(pk=pk)
    except:
        return HttpResponse(status=404) 

    if(request.method == 'PUT'):
        data = JSONParser().parse(request) 
        serializer = TaskSerializer(study, data=data)
        if(serializer.is_valid()):  
            serializer.save() 
            return JsonResponse(serializer.data, status=201)

        return JsonResponse(serializer.errors, status=400)




