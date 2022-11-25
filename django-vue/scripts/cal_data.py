from auto.models import Mouse, FedDataRaw, FedDataByHour, FedDataByDay, Cohort, FedDataRolling
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Avg, F, RowRange, Window

def run():

    # goal load raw data
    m = Mouse.objects.get(pk=6)
    d = date(year=2022, month=3, day=26)

    # count day since start
    #q = Cohort.objects.filter(fed__mouse__id=m.id)
    #delta_day = d - q[0].startDate

    # cal by Hour, by Day results and save into tables
    # given one day, one mouse
    #cal_hr_day(m, d) 

    # cal by Poke result and save into table
    #cal_rolling_avg(m, d)
    #cal_rolling(m, d, 30)

def cal_hr_day(m, d):
    qs = FedDataRaw.objects.filter(mouse=m, actTimestamp__date=d)

    # get active poke
    active_poke = qs[0].activePoke  
    onset_timestamp = qs[1].actTimestamp # onset from the second transaction

    pre_l=0
    pre_r=0
    pre_p=0
    for hr in range(8):
        qs_hr = qs.filter(actTimestamp__lte=(onset_timestamp+timedelta(hours=hr+1)))
        qs_hr_last = qs_hr.latest('actTimestamp')
        
        cur_l = qs_hr_last.leftPokeCount - pre_l
        cur_r = qs_hr_last.rightPokeCount - pre_r
        cur_p = qs_hr_last.pelletCount - pre_p

        # count poke acc
        poke_acc=0;
        if cur_l+cur_r == 0:
            poke_acc=0;
        elif active_poke == 1: # left
            poke_acc = cur_l / (cur_l+cur_r)
        elif active_poke == 2: #right
            poke_acc = cur_r / (cur_l+cur_r)
        else:
            raise Exception("Invalid active_poke code.") 

        # insert into db
        fedhr = FedDataByHour(leftPokeCount=cur_l, rightPokeCount=cur_r, pelletCount=cur_p, activePoke=active_poke, pokeAcc=poke_acc, startTime=onset_timestamp+timedelta(hours=hr), endTime=onset_timestamp+timedelta(hours=hr+1), numHour=hr+1, fedDate=d, mouse=m)
        fedhr.save()

        # update pre_l, pre_r, pre_p 
        pre_l = qs_hr_last.leftPokeCount
        pre_r = qs_hr_last.rightPokeCount
        pre_p = qs_hr_last.pelletCount

        # insert into day table
        if hr == 7: 
            poke_acc=0;
            if (qs_hr_last.leftPokeCount+qs_hr_last.rightPokeCount) == 0:
                poke_acc=0;
            elif active_poke == 1: # left
                poke_acc = qs_hr_last.leftPokeCount / (qs_hr_last.leftPokeCount+qs_hr_last.rightPokeCount)
            elif active_poke == 2: #right
                poke_acc = qs_hr_last.rightPokeCount / (qs_hr_last.leftPokeCount+qs_hr_last.rightPokeCount)
            else:
                raise Exception("Invalid active_poke code.") 

            fedday = FedDataByDay(leftPokeCount=qs_hr_last.leftPokeCount, rightPokeCount=qs_hr_last.rightPokeCount, pelletCount=qs_hr_last.pelletCount, activePoke=active_poke, pokeAcc=poke_acc, fedDate=d, mouse=m)
            fedday.save()

def cal_rolling_avg(m, d):
    qs = FedDataRaw.objects.filter(mouse=m, actTimestamp__date=d)

    # get active poke
    active_poke = qs[0].activePoke  

    # get onset time
    total_qs = len(qs)
    onset_index = 16
    for i in range(len(qs)):
        if qs[onset_index+i].event == 2:
            continue
        else:
            onset_index = onset_index+i
            break
    onset_time = qs[onset_index].actTimestamp

    qs_poke = FedDataRaw.objects.filter(mouse=m, actTimestamp__date=d, event=1, actTimestamp__gte=onset_time)
    #print(len(qs_poke))

    #count qs_acc
    for i in range(len(qs_poke)):
        lc = qs_poke[i].leftPokeCount
        rc = qs_poke[i].rightPokeCount
        ts = qs_poke[i].actTimestamp

        poke_acc=0;
        if lc+rc == 0:
            poke_acc=0;
        elif active_poke == 1: # left
            poke_acc = lc / (lc+rc)
        elif active_poke == 2: #right
            poke_acc = rc / (lc+rc)
        else:
            raise Exception("Invalid active_poke code.") 

        fdr = FedDataRolling(pokeAcc=poke_acc, windowSize=1, startTime=ts, endTime=ts, fedDate=d, mouse=m)
        fdr.save()


def cal_rolling(m, d, win_size):
    #start rolling
    #https://stackoverflow.com/questions/48790322/fast-moving-average-computation-with-django-orm
    items = FedDataRolling.objects.filter(windowSize=1, mouse=m, fedDate=d).annotate(
            avg=Window(
                expression=Avg('pokeAcc'), 
                order_by=F('id').asc(), 
                frame=RowRange(start=(0-win_size+1),end=0)
                )
            )

    #print(items[29].avg)
    for i in range(win_size-1, len(items)):
        avg = items[i].avg
        fdr = FedDataRolling(pokeAcc=avg, windowSize=win_size, startTime=items[i-(win_size-1)].startTime, endTime=items[i].startTime, fedDate=d,mouse=m)
        fdr.save()


