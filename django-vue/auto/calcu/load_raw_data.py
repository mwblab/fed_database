from datetime import datetime, timedelta
from django.utils import timezone
import pandas as pd
import pytz
import math
import os, sys
from auto.models import Mouse, FedDataRaw, Fed, FedDataTestType
import re

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

# FEDXXX_MMDDYY_XX_D4_FR3
def validate_uploaded_filename(csv_path):
    file_name = os.path.basename(csv_path)
    file_name_wo_ext = os.path.splitext(file_name)[0]

    pattern = re.compile("FED\d{3}_\d{6}_\w{1,2}_D\d{1,3}_[\w_]+")

    if not pattern.fullmatch( file_name_wo_ext ) :
        # deal with upload random suffix
        file_name_sp = file_name_wo_ext.split("_")
        if len(file_name_sp[-1]) >= 5 and len(file_name_sp[-1]) <= 8:
            file_name_wo_ext = "_".join(file_name_sp[:-1])
        else:
            file_name_wo_ext = "_".join(file_name_sp)

        raise Exception("%s.csv filename format is not correct. Please follow the format: FEDXXX_MMDDYY_XX_DX_CODE and upload again." % (file_name_wo_ext))

    m = re.match(r"FED\d{3}_(\d{6})_\w{1,2}_D\d{1,3}_[\w_]+", file_name_wo_ext)
    date_format = '%m%d%y'
    mdy = m.group(1)
    try:
        # formatting the date using strptime() function
        dateObject = datetime.strptime(mdy, date_format)
    # If the date validation goes wrong
    except ValueError:
        raise Exception("%s.csv filename MMDDYY format is not correct. Not a valid month, day or year." % (file_name_wo_ext))


# sample: FED###_MMDDYY_D#_CODE => FEDXXX_MMDDYY_XX_D4_FR3
def get_mouse_obj(csv_path, cohort_id):
    file_name = os.path.basename(csv_path)
    file_name_wo_ext = os.path.splitext(file_name)[0]
    file_name_sp = file_name_wo_ext.split("_", 4)

    try:
        #q = Mouse.objects.select_related('fed').get(fedDisplayName = "FED%03d" % devNum )
        ret_fed = Fed.objects.get(fedDisplayName = "%s" % file_name_sp[0], cohort_id = cohort_id)
        ret_mouse = Mouse.objects.get(fed=ret_fed)
        return ret_mouse
    except Fed.DoesNotExist as err: 
        # insert new fed and ini new mouse
        # what if new cohort?
        new_fed = Fed(cohort_id = cohort_id, fedDisplayName = "%s" % file_name_sp[0])
        new_fed.save()

        new_mouse = Mouse( mouseDisplayName="Cage.Animal", genotype="WT", fed=new_fed, dob=timezone.make_aware(datetime.now()) )
        new_mouse.save()
        return new_mouse
    except Mouse.DoesNotExist as err:
        new_mouse = Mouse( mouseDisplayName="Cage.Animal", genotype="WT", fed=ret_fed, dob=timezone.make_aware(datetime.now()) )
        new_mouse.save()
        return new_mouse
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise


# sample: FED###_MMDDYY_D#_CODE (deprecated)
# FEDXXX_MMDDYY_XX_D4_FR3
# tbd: key error handling
def import_fed_csv(csv_path, ret_mouse):
    cut_off_hr = 8
    start_timestamp = 0

    # parse test_type, day, mmddyy
    file_name = os.path.basename(csv_path)
    file_name_wo_ext = os.path.splitext(file_name)[0]
    file_name_sp = file_name_wo_ext.split("_", 4)

    date_string = file_name_sp[1]

    day_string = file_name_sp[3]
    num_day = int(day_string[1:])

    # deal with upload random suffix
    test_type_sp = file_name_sp[-1].split("_")
    if len(test_type_sp[-1]) >= 5 and len(test_type_sp[-1]) <= 8:
        test_type = "_".join(test_type_sp[:-1])
    else:
        test_type = "_".join(test_type_sp)
    if test_type in ['FR1', 'FR3', '3R', 'PR', '3R_PR', 'PR_X', '3R_PR_X', 'QU', '3R_QU', 'QU_X', '3R_QU_X', 'E', 'RE', 'FF', 'FR5']:
        try:
            FedDataTestType.objects.get(fedNumDay=num_day, mouse=ret_mouse)
        except FedDataTestType.DoesNotExist as err: 
            # insert
            fdtt = FedDataTestType(testType=test_type, fedNumDay=num_day, mouse=ret_mouse)
            fdtt.save()
        except FedDataTestType.MultipleObjectsReturned as err:
            pass
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

        # set cut_off
        if test_type in ['QU', 'QU_X', 'E']:
            cut_off_hr = 4

    #print(num_day)
    #print(test_type)

    f = pd.read_csv(csv_path)
    f = f.rename(columns={' Event': 'Event', ' Active_Poke': 'Active_Poke', ' Retrieval_Time': 'Retrieval_Time', ' Left_Poke_Count': 'Left_Poke_Count', ' Right_Poke_Count': 'Right_Poke_Count', ' Pellet_Count': 'Pellet_Count', ' MM:DD:YYYY hh:mm:ss':'MM:DD:YYYY hh:mm:ss', ' Battery_Voltage': 'Battery_Voltage', ' Motor_Turns': 'Motor_Turns', ' Session_Type': 'Session_Type', 'Session_type': 'Session_Type' })

    # validate headers
    for hdr in ['Event', 'Active_Poke', 'Retrieval_Time', 'Left_Poke_Count', 'Right_Poke_Count', 'Pellet_Count', 'Battery_Voltage', 'Motor_Turns', 'Session_Type']:
        if hdr not in f.iloc[0,:].index:
            raise Exception("%s header is missing" % hdr)

    for i in range(f.shape[0]):
        r = f.iloc[i,:]
        #print(r.index)

        et = 0
        if r["Event"] == "Poke" or r["Event"] == "Left" or r["Event"] == "Right":
            et = 1
        elif r["Event"] == "Pellet":
            et = 2
        elif r["Event"] == "LeftWithPellet" or r["Event"] == "RightWithPellet": # new event, no use atm
            et = 3
        elif r["Event"] == "LeftDuringDispense" or r["Event"] == "RightDuringDispense": # new event, no use atm
            et = 4
        elif r["Event"] == "LeftShort" or r["Event"] == "RightShort": # new event, no use atm
            et = 5
        elif r["Event"] == "LeftinTimeout" or r["Event"] == "RightinTimeout": # new event, no use atm
            et = 6
        else:
            raise Exception("Event value is not matched: '%s'" % r["Event"])

        ap = 0
        if r["Active_Poke"] == "Left" and et < 3: # actual poke
            ap = 1
        elif r["Active_Poke"] == "Right" and et < 3: # actual poke
            ap = 2
        elif r["Active_Poke"] == "Left" and et == 3: # poke with pellet, new event
            ap = -1
        elif r["Active_Poke"] == "Right" and et == 3: # poke with pellet, new event
            ap = -2
        elif r["Active_Poke"] == "Left" and et == 4: # new event
            ap = -3
        elif r["Active_Poke"] == "Right" and et == 4: # new event
            ap = -4
        elif r["Active_Poke"] == "Left" and et == 5: # new event
            ap = -5
        elif r["Active_Poke"] == "Right" and et == 5: # new event
            ap = -6
        elif r["Active_Poke"] == "Left" and et == 6: # new event
            ap = -7
        elif r["Active_Poke"] == "Right" and et == 6: # new event
            ap = -8
        else:
            raise Exception("Active_Poke value is not matched: '%s'" % r["Active_Poke"])

        rt = r["Retrieval_Time"]
        if rt == "Timed_Out" or rt == "Timed_out":
            rt = -1
        elif math.isnan(float(rt)):
            rt = -1
        else:
            rt = round(float(rt))
        
        # validate data string
        pattern = re.compile(".*? \d{1,2}:\d{1,2}:\d{1,2}")
        if not pattern.fullmatch( r["MM:DD:YYYY hh:mm:ss"] ) :
            raise Exception("hh:mm:ss values are not correct.")
        m = re.match(r".*? (\d{1,2}):(\d{1,2}):(\d{1,2})", r["MM:DD:YYYY hh:mm:ss"])
        if int(m.group(1)) <= -1 or int(m.group(1)) >=25 or int(m.group(2)) <= -1 or int(m.group(2)) >= 60 or int(m.group(3)) <= -1 or int(m.group(3)) >= 60:
            raise Exception("hh:mm:ss values are not correct. One of them is not a valid sec, minute or hour.")

        current_timestamp = str2datetime(r["MM:DD:YYYY hh:mm:ss"], date_string)
        if i == 0:
            start_timestamp = current_timestamp
            fd = FedDataRaw(actTimestamp=current_timestamp, actNumDay=num_day, deviceNumber=file_name_sp[0][3:], batteryVol=r["Battery_Voltage"], motorTurns=r["Motor_Turns"], sessionType=r["Session_Type"], event=et, activePoke=ap, leftPokeCount=r["Left_Poke_Count"], rightPokeCount=r["Right_Poke_Count"], pelletCount=r["Pellet_Count"], retrievalTime=rt, mouse=ret_mouse)
            fd.save()
        elif current_timestamp < start_timestamp + timedelta(hours=cut_off_hr):
            fd = FedDataRaw(actTimestamp=current_timestamp, actNumDay=num_day, deviceNumber=file_name_sp[0][3:], batteryVol=r["Battery_Voltage"], motorTurns=r["Motor_Turns"], sessionType=r["Session_Type"], event=et, activePoke=ap, leftPokeCount=r["Left_Poke_Count"], rightPokeCount=r["Right_Poke_Count"], pelletCount=r["Pellet_Count"], retrievalTime=rt, mouse=ret_mouse)
            fd.save()


# tbd: split error handling
def str2datetime(str, date_string):
    s1 = str.split(" ")
    #date_sp = s1[0].split("/")
    time_sp = s1[1].split(":")

    # https://hunj.dev/django-timezone-aware-datetime-objects/
    return timezone.make_aware(datetime(2000+int(date_string[4:6]), int(date_string[0:2]), int(date_string[2:4]), int(time_sp[0]), int(time_sp[1]), int(time_sp[2]), microsecond=0))


