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
import os, sys
import openpyxl
from auto.models import Mouse, FedDataRaw, Fed, FedDataTestType
from django.utils import timezone
from datetime import datetime, timedelta

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

            error_msg_all = ''
            for f in file_list: 
                file_path = "media/" + f
                mouse_data = {}
                try:
                    # validate format
                    load_raw_data.validate_uploaded_filename(file_path)
                    # remove data mice at that day
                    ret_mouse = load_raw_data.get_mouse_obj(file_path , cohort_id)
                    mouse_data['del_mouse_id'] = ret_mouse.id
                    # parse num_day 
                    file_name = os.path.basename(file_path)
                    file_name_wo_ext = os.path.splitext(file_name)[0]
                    file_name_sp = file_name_wo_ext.split("_", 4)
                    day_string = file_name_sp[3]
                    num_day = int(day_string[1:])
                    mouse_data['del_start_day'] = num_day
                    mouse_data['del_end_day'] = num_day
                    cal_data.del_mouse_data_fun(mouse_data)

                    # upload cur file
                    load_raw_data.import_fed_csv(file_path, ret_mouse)
                except Exception as e:
                    # save error msg
                    error_msg_all += os.path.basename(file_path) + ": "
                    error_msg_all += str(e) + "\n"

                    # remove data mice at that day
                    if 'del_end_day' in mouse_data:
                        cal_data.del_mouse_data_fun(mouse_data)
                    pass

            if error_msg_all != '':
                e_data = {
                        'error': 'Upload batch files failure',
                        'message': '%s' % (error_msg_all)
                }
                return JsonResponse(e_data, status=400)
            else:
                return HttpResponse(status=201) 
        except Exception as e:
            print(e)
            e_data = {
                'error': 'Upload failure',
                'message': '%s' % (str(e))
            }
            return JsonResponse(e_data, status=400)
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
            e_data = {
                'error': 'Calculate failure',
                'message': 'unable to calculate results due to %s' % (e)
            }
            return JsonResponse(e_data, status=400)

@csrf_exempt
def proc_acq(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            ret = cal_data.cal_acq(int(data['cId']), data['time_acq_picker'], int(data['time_acq_range']), int(data['cri_num_p_day_m']), int(data['cri_num_p_day_f']), float(data['cri_end_day_acc_m']), float(data['cri_end_day_acc_f']), float(data['cri_max_rol_avg30_m']), float(data['cri_max_rol_avg30_f']), float(data['cri_stab_yes_m']), float(data['cri_stab_yes_f']), int(data['cri_rt_thres_m']), int(data['cri_rt_thres_f']), data['cri_filter_test_type'], float(data['cri_rol_poke_m']), float(data['cri_rol_poke_f']), int(data['cri_rol_poke_w_size'])  )
            #print(ret)
            return JsonResponse(ret, safe=False, status=201)
            # safe=False explain https://dev.to/chryzcode/django-json-response-safe-false-4f9i
        except Exception as e:
            e_data = {
                'error': 'Show failure',
                'message': 'unable to show table due to %s' % (e)
            }
            return JsonResponse(e_data, status=400)

@csrf_exempt
def get_cohort_list(request):
    if(request.method == 'GET'):
        try:
            ret = cal_data.get_cohort_list_fun(1)
            return JsonResponse(ret, safe=False, status=201)
        except Exception as e:
            print(e)
            return JsonResponse({'error':str(e)}, safe=False, status=400) 

@csrf_exempt
def put_new_cohort(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            ret = cal_data.put_new_cohort_fun(data)
            return JsonResponse(ret, safe=False, status=201)
        except Exception as e:
            print(e)
            return JsonResponse({'error':str(e)}, safe=False, status=400) 

@csrf_exempt
def del_cohort(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            ret = cal_data.del_cohort_fun(data)
            return JsonResponse(ret, safe=False, status=201)
        except Exception as e:
            print(e)
            return JsonResponse({'error':str(e)}, safe=False, status=400) 

@csrf_exempt
def get_mouse_list(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            ret = cal_data.get_mouse_list_fun(data['cohort_id'])
            return JsonResponse(ret, safe=False, status=201)
        except Exception as e:
            print(e)
            return JsonResponse({'error':str(e)}, safe=False, status=400) 

@csrf_exempt
def put_mouse_list(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            ret = cal_data.put_mouse_list_fun(data)
            return JsonResponse(ret, safe=False, status=201)
        except Exception as e:
            print(e)
            return JsonResponse({'error':str(e)}, safe=False, status=400) 


@csrf_exempt
def del_mouse_data(request):
    if(request.method == 'POST'):
        try:
            # decode json
            data = JSONParser().parse(request) 
            ret = cal_data.del_mouse_data_fun(data)
            return JsonResponse(ret, safe=False, status=201)
        except Exception as e:
            print(e)
            return JsonResponse({'error':str(e)}, safe=False, status=400) 

# upload prefill file
@csrf_exempt
def upload_prefill_file(request): 
    if(request.method == 'POST'):
        try:
            error_msg_all = ''

            uploaded_file = request.FILES.get('fileList')  # matches FormData key
            cohort_id = request.POST.get('cId')
            #print("cohort id:", c_id)
            #print("prefill file:", uploaded_file)
            prefill_content = uploaded_file.read()
            
            # parse file content
            wb = openpyxl.load_workbook(uploaded_file)
            sheet = wb.active
            # skip header

            for row in sheet.iter_rows(min_row=2, values_only=True):
                fed_id = row[0]
                mouse_name = row[1]
                mouse_sex = row[2]
                mouse_genotype = row[3]
                # create a new mouse if not exists in c_id
                try:
                    ret_fed = Fed.objects.get(fedDisplayName = "%s" % fed_id, cohort_id = cohort_id)
                    ret_mouse = Mouse.objects.get(fed=ret_fed)

                    # if fed and mouse exist, update mouse info
                    ret_mouse.mouseDisplayName = mouse_name
                    ret_mouse.genotype = mouse_genotype
                    ret_mouse.sex = mouse_sex
                    ret_mouse.save()

                except Fed.DoesNotExist as err: 
                    # insert new fed and ini new mouse
                    # what if new cohort?
                    new_fed = Fed(cohort_id = cohort_id, fedDisplayName = "%s" % fed_id)
                    new_fed.save()

                    new_mouse = Mouse( mouseDisplayName=mouse_name, sex=mouse_sex, genotype=mouse_genotype, fed=new_fed, dob=timezone.make_aware(datetime.now()) )
                    new_mouse.save()
                except Mouse.DoesNotExist as err:
                    new_mouse = Mouse( mouseDisplayName=mouse_name, sex=mouse_sex, genotype=mouse_genotype, fed=ret_fed, dob=timezone.make_aware(datetime.now()) )
                    new_mouse.save()
                except Exception as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    raise
        except Exception as e:
            # save error msg
            error_msg_all += os.path.basename(uploaded_file) + ": "
            error_msg_all += str(e) + "\n"
            pass

    if error_msg_all != '':
        e_data = {
            'error': 'Upload pre-fill files failure',
            'message': '%s' % (error_msg_all)
            }
        return JsonResponse(e_data, status=400)
    else:
        return HttpResponse(status=201) 
    
