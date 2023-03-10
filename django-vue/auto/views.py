from django.shortcuts import render

# parsing data from the client
from rest_framework.parsers import JSONParser
# To bypass having a CSRF token
from django.views.decorators.csrf import csrf_exempt
# for sending response to the client
from django.http import HttpResponse, JsonResponse
# API definition for task
from .serializers import TaskSerializer
from .models import Study
from auto.calcu import load_raw_data, cal_data

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


# data_load
@csrf_exempt
def proc_data_load(request): 
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            cohort_id = int(data['cId'])
            num_day = int(data['numDay'])
            file_list = data['fileList']
            for f in file_list: 
                file_path = "media/" + f
                ret_mouse = load_raw_data.get_mouse_obj(file_path , cohort_id)
                load_raw_data.import_fed_csv(file_path, ret_mouse)
            return HttpResponse(status=201) 
        except Exception as e:
            print(e)
            return HttpResponse(status=400) 
# cal
@csrf_exempt
def proc_cal(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            cohort_id = int(data['cId'])
            cal_data.proc_run(cohort_id)
            return HttpResponse(status=201) 
        except Exception as e:
            print(e)
            return HttpResponse(status=400) 

@csrf_exempt
def proc_acq(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            ret = cal_data.cal_acq(int(data['cId']), data['time_acq_picker'], int(data['time_acq_range']), int(data['cri_num_p_day_m']), int(data['cri_num_p_day_f']), float(data['cri_end_day_acc_m']), float(data['cri_end_day_acc_f']), float(data['cri_max_rol_avg30_m']), float(data['cri_max_rol_avg30_f']), float(data['cri_stab_yes_m']), float(data['cri_stab_yes_f']) )
            #print(ret)
            return JsonResponse(ret, safe=False, status=201)
        except Exception as e:
            print(e)
            return HttpResponse(status=400) 

