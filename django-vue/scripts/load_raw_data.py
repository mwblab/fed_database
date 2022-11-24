from auto.models import Mouse, FedDataRaw
from datetime import datetime
from django.utils import timezone
import pandas as pd
import pytz
import math
import os

def run():

    # loop through target dir
    day_dir = "./d21"   
    dirs = os.listdir( day_dir )

    # for each csv
    # get fed number, date, cohortID, studyID, mouseID
    for file in dirs:
        # check if size >0, with csv extension
        split_tup = os.path.splitext(file)

        file_fp = os.path.join(day_dir,file)
        fs = os.stat(file_fp)
        if fs.st_size > 0 and split_tup[1].lower() == ".csv":
            print(file_fp)
            import_fed_csv(file_fp)


def import_fed_csv(csv_path):

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
        
        m = Mouse.objects.get(pk=1)
        fd = FedDataRaw(actTimestamp=str2datetime(r[0]), deviceNumber=r[1], batteryVol=r[2], motorTurns=r[3], sessionType=r[4], event=et, activePoke=ap, leftPokeCount=r[" Left_Poke_Count"], rightPokeCount=r[" Right_Poke_Count"], pelletCount=r[" Pellet_Count"], retrievalTime=rt, mouse=m)
        fd.save()



def str2datetime(str):
    s1 = str.split(" ")
    date_sp = s1[0].split("/")
    time_sp = s1[1].split(":")

    # https://hunj.dev/django-timezone-aware-datetime-objects/
    return timezone.make_aware(datetime(int(date_sp[2]), int(date_sp[0]), int(date_sp[1]), int(time_sp[0]), int(time_sp[1]), int(time_sp[2]), microsecond=0))


