from auto.models import Mouse, FedDataRaw, FedDataByHour, FedDataByDay, Cohort
from datetime import datetime, date, timedelta
from django.utils import timezone

def run():

    # goal load raw data
    m = Mouse.objects.get(pk=6)
    d = date(year=2022, month=3, day=26)

    # count day since start
    q = Cohort.objects.filter(fed__mouse__id=m.id)
    delta_day = d - q[0].startDate

    # cal by Hour, by Day results and save into tables
    # given one day, one mouse
    cal_hr_day(m, d, delta_day.days) 

    # cal by Poke result and save into table
    #cal_poke()

def cal_hr_day(m, d, ddays):
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
        fedhr = FedDataByHour(leftPokeCount=cur_l, rightPokeCount=cur_r, pelletCount=cur_p, activePoke=active_poke, pokeAcc=poke_acc, startTime=onset_timestamp+timedelta(hours=hr), endTime=onset_timestamp+timedelta(hours=hr+1), numHour=hr+1, fedDate=d, fedDaySinceCohortStart=ddays, mouse=m)
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

            fedday = FedDataByDay(leftPokeCount=qs_hr_last.leftPokeCount, rightPokeCount=qs_hr_last.rightPokeCount, pelletCount=qs_hr_last.pelletCount, activePoke=active_poke, pokeAcc=poke_acc, fedDate=d, fedDaySinceCohortStart=ddays, mouse=m)
            fedday.save()
 
#def cal_poke(mouse, cal_timestamp):




