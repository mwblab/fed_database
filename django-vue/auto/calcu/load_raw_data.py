from datetime import datetime
from django.utils import timezone
import pandas as pd
import pytz
import math
import os, sys
from auto.models import Mouse, FedDataRaw, Fed, FedDataTestType

def run():

    #given cohort id
    cohort_id = 1

    # loop through target dir
    day_dir = "./d21"   
    dirs = os.listdir( day_dir )

    # for each csv
    for file in dirs:

        # check if size >0, with csv extension
        split_tup = os.path.splitext(file)

        file_fp = os.path.join(day_dir,file)
        fs = os.stat(file_fp)
        if fs.st_size > 0 and split_tup[1].lower() == ".csv":
            # debug
            print(file_fp)

            # get mouse 
            ret_mouse = get_mouse_obj(file_fp, cohort_id)
            
            # import csv
            import_fed_csv(file_fp, ret_mouse)


def get_mouse_obj(csv_path, cohort_id):
    f = pd.read_csv(csv_path)
    r = f.iloc[0,:]
    devNum = r[1]
            
    try:
        #q = Mouse.objects.select_related('fed').get(fedDisplayName = "FED%03d" % devNum )
        ret_fed = Fed.objects.get(fedDisplayName = "FED%03d" % devNum, cohort_id = cohort_id)
        ret_mouse = Mouse.objects.get(fed=ret_fed)
        return ret_mouse
    except Fed.DoesNotExist as err: 
        # insert new fed and ini new mouse
        # what if new cohort?
        new_fed = Fed(cohort_id = cohort_id, fedDisplayName = "FED%03d" % devNum)
        new_fed.save()

        new_mouse = Mouse( mouseDisplayName="Cage.Animal", genotype="", fed=new_fed, dob=timezone.make_aware(datetime.now()) )
        new_mouse.save()
        return new_mouse
    except Mouse.DoesNotExist as err:
        new_mouse = Mouse( mouseDisplayName="Cage.Animal", genotype="", fed=ret_fed, dob=timezone.make_aware(datetime.now()) )
        new_mouse.save()
        return new_mouse
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise



# tbd: key error handling
def import_fed_csv(csv_path, ret_mouse, num_day):

    f = pd.read_csv(csv_path)

    for i in range(f.shape[0]):
        r = f.iloc[i,:]
        #print(r.index)

        et = 0
        if r[" Event"] == "Poke":
            et = 1
        elif r[" Event"] == "Pellet":
            et = 2
        else:
            raise Exception("Event value is not matched: '%s'" % r[" Event"])

        ap = 0
        if r[" Active_Poke"] == "Left":
            ap = 1
        elif r[" Active_Poke"] == "Right":
            ap = 2
        else:
            raise Exception("Active_Poke value is not matched: '%s'" % r[" Active_Poke"])

        rt = r[" Retrieval_Time"]
        if math.isnan(rt):
            rt = -1
        else:
            rt = int(rt)
        
        fd = FedDataRaw(actTimestamp=str2datetime(r[0]), actNumDay=num_day, deviceNumber=r[1], batteryVol=r[2], motorTurns=r[3], sessionType=r[4], event=et, activePoke=ap, leftPokeCount=r[" Left_Poke_Count"], rightPokeCount=r[" Right_Poke_Count"], pelletCount=r[" Pellet_Count"], retrievalTime=rt, mouse=ret_mouse)
        fd.save()

    # get filename
    file_name = os.path.basename(csv_path)
    file_name_wo_ext = os.path.splitext(file_name)[0]
    file_name_sp = file_name_wo_ext.split("_")
    test_type = file_name_sp[-1]
    if len(test_type) >= 5 and len(test_type) <= 8:
        test_type = file_name_sp[-2]
    if test_type in ['PR', 'QU', 'FR3', 'FR3R', 'EXT', 'REI']:
        # insert
        fdtt = FedDataTestType(testType=test_type, fedNumDay=num_day, mouse=ret_mouse)
        fdtt.save()

# tbd: split error handling
def str2datetime(str):
    s1 = str.split(" ")
    date_sp = s1[0].split("/")
    time_sp = s1[1].split(":")

    # https://hunj.dev/django-timezone-aware-datetime-objects/
    return timezone.make_aware(datetime(int(date_sp[2]), int(date_sp[0]), int(date_sp[1]), int(time_sp[0]), int(time_sp[1]), int(time_sp[2]), microsecond=0))


