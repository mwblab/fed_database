from auto.models import Mouse, FedDataRaw, FedDataByHour, FedDataByDay, Cohort, FedDataRolling, Data, Fed, Study, FedDataTestType
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Avg, F, RowRange, Window

def run():

    # del feddatabyday, feddatabyhour, feddatarolling, feddataraw
    FedDataRolling.objects.all().delete()
    FedDataByHour.objects.all().delete()
    FedDataByDay.objects.all().delete()
    FedDataRaw.objects.all().delete()
    FedDataTestType.objects.all().delete()

    # del data upload log (data table)
    Data.objects.all().delete()

    # del mouse (id!=1), fed (id!=1), cohort (id!=1), study (id!=1) 
    Mouse.objects.filter(id__gt=1).delete()
    Fed.objects.filter(id__gt=1).delete()
    Cohort.objects.filter(id__gt=1).delete()
    Study.objects.filter(id__gt=1).delete()
    
