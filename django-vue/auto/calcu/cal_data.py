from auto.models import Mouse, FedDataRaw, FedDataByHour, FedDataByDay, Cohort, FedDataRolling
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Avg, F, RowRange, Window, Max
from django.db.models.functions import TruncDate

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

def proc_run(cohort_id):
    mouse_list = get_mouse_list(cohort_id)
    # for each mouse, find cal day
    for m in mouse_list:
        day_set = get_day_set(m)
        for d_str in day_set: 
            d_str_sp = d_str.split('-')
            d = date(year=int(d_str_sp[2]), month=int(d_str_sp[0]), day=int(d_str_sp[1]))
            print(m)
            print(d)
            print("cal_hr_day")
            cal_hr_day(m, d)
            print("cal_rolling_1")
            cal_rolling_avg(m, d)
            print("cal_rolling_window")
            cal_rolling(m, d, 30)

def get_mouse_list(cohort_id):
    qs = Mouse.objects.filter(fed__cohort_id=cohort_id)
    return list(qs) 

def get_day_set(m):
    trans_from_caled_day = FedDataByDay.objects.filter(mouse=m).order_by('fedDate')
    trans_from_raw = FedDataRaw.objects.filter(mouse=m).values(feddate=TruncDate('actTimestamp')).annotate(Max('feddate')).order_by('feddate')
    trans_from_caled_day_set = set()
    for t in trans_from_caled_day:
        date_time = t.fedDate.strftime("%m-%d-%Y")
        trans_from_caled_day_set.add(date_time)

    trans_from_raw_set = set()
    for t in trans_from_raw:
        date_time = t['feddate'].strftime("%m-%d-%Y")
        trans_from_raw_set.add(date_time)

    return(trans_from_raw_set-trans_from_caled_day_set)

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

def cal_acq(cohort_id, time_acq_picker, time_acq_range, cri_num_p_day_m, cri_num_p_day_f, cri_end_day_acc, cri_max_rol_avg30, cri_stab_yes):
    window_size = 30   

    # get data of all days and mouses, day based
    pick_date_end = date.fromisoformat(time_acq_picker)
    pick_date_start = pick_date_end + timedelta(days=-time_acq_range)
    
    # get day
    qs_day = FedDataByDay.objects.filter(mouse__fed__cohort_id=cohort_id, fedDate__range=[pick_date_start, pick_date_end])
    # get rolling day info, different structure
    qs_rol = FedDataRolling.objects.filter(mouse__fed__cohort_id=cohort_id, fedDate__range=[pick_date_start, pick_date_end], windowSize=window_size).values('fedDate', 'mouse_id').annotate(rollMaxPokeAcc=Max('pokeAcc'))

    # get mouse list
    mouse_list = Mouse.objects.filter(fed__cohort_id=cohort_id).order_by('id')

    # final output
    cri_num_p_day_raw = []
    cri_num_p_day_binary = []
    cri_end_day_acc_raw = []
    cri_end_day_acc_binary = []
    cri_max_rol_avg30_raw = []
    cri_max_rol_avg30_binary = []
    cri_stab_yes_raw = []
    cri_stab_yes_binary = []
    cri_acq_sum = []
    cri_acq_binary = []

    # init mouse, day na table
    for m in mouse_list:
        # generate one row
        roll_raw = {}
        roll_raw['mouse_id'] = m.id
        roll_raw['mouse_name'] = m.mouseDisplayName
        roll_raw['genotype'] = m.genotype

        if m.sex == 0:
            roll_raw['sex'] = 'na'
        elif m.sex == 1:
            roll_raw['sex'] = 'male'
        elif m.sex == 2:
            roll_raw['sex'] = 'female'
        else:
            roll_raw['sex'] = m.sex

        # num_p_day
        # cri_stab_yes_binary
        roll_raw['dataType'] = "num_p_day_raw"
        roll_raw['threshold'] = "M:%d F:%d" % (cri_num_p_day_m, cri_num_p_day_f)
        roll_stab = roll_raw.copy()
        roll_stab['dataType'] = "stab_yes_binary"
        roll_stab['threshold'] = cri_stab_yes
        for dd in range(time_acq_range):
            d = pick_date_start + timedelta(days=dd+1)

            qs_day_m_day = qs_day.filter(mouse=m, fedDate=d)
            roll_stab[d.isoformat()] = 0
            if qs_day_m_day.exists():
                roll_raw[d.isoformat()] = qs_day_m_day[0].pelletCount

                if dd > 0:
                    pre_day = pick_date_start + timedelta(days=dd)
                    if roll_raw[pre_day.isoformat()] != 'na':
                        pre_day_count = roll_raw[pre_day.isoformat()]
                        max_pre_day_count = pre_day_count + pre_day_count*cri_stab_yes
                        min_pre_day_count = pre_day_count - pre_day_count*cri_stab_yes
                        if roll_raw[d.isoformat()] >= min_pre_day_count and roll_raw[d.isoformat()] <= max_pre_day_count:
                            roll_stab[d.isoformat()] = 1
            else:
                roll_raw[d.isoformat()] = 'na'
        cri_num_p_day_raw.append(roll_raw.copy())
        cri_stab_yes_binary.append(roll_stab.copy())

        roll_raw['dataType'] = "num_p_day_binary"
        roll_raw['threshold'] = "M:%d F:%d" % (cri_num_p_day_m, cri_num_p_day_f)
        for dd in range(time_acq_range):
            d = pick_date_start + timedelta(days=dd+1)

            if m.sex == 1:
                qs_day_m_day = qs_day.filter(mouse=m, fedDate=d, pelletCount__gte = cri_num_p_day_m )
            elif m.sex == 2:
                qs_day_m_day = qs_day.filter(mouse=m, fedDate=d, pelletCount__gte = cri_num_p_day_f )
            else:
                qs_day_m_day = None

            if qs_day_m_day and qs_day_m_day.exists():
                roll_raw[d.isoformat()] = 1
            else:
                roll_raw[d.isoformat()] = 0
        cri_num_p_day_binary.append(roll_raw.copy())
        

        #cri_end_day_acc
        roll_raw['dataType'] = "end_day_acc_raw"
        roll_raw['threshold'] = cri_end_day_acc
        for dd in range(time_acq_range):
            d = pick_date_start + timedelta(days=dd+1)
            qs_day_m_day = qs_day.filter(mouse=m, fedDate=d)
            if qs_day_m_day.exists():
                roll_raw[d.isoformat()] = qs_day_m_day[0].pokeAcc
            else:
                roll_raw[d.isoformat()] = 'na'
        cri_end_day_acc_raw.append(roll_raw.copy())
        roll_raw['dataType'] = "end_day_acc_binary"
        roll_raw['threshold'] = cri_end_day_acc
        for dd in range(time_acq_range):
            d = pick_date_start + timedelta(days=dd+1)
            qs_day_m_day = qs_day.filter(mouse=m, fedDate=d, pokeAcc__gt = cri_end_day_acc)
            if qs_day_m_day and qs_day_m_day.exists():
                roll_raw[d.isoformat()] = 1
            else:
                roll_raw[d.isoformat()] = 0
        cri_end_day_acc_binary.append(roll_raw.copy())

                
        # max10_ralling_30
        roll_raw['dataType'] = "max10_rolling_30_raw"
        roll_raw['threshold'] = cri_max_rol_avg30
        for dd in range(time_acq_range):
            d = pick_date_start + timedelta(days=dd+1)
            qs_rol_m_day = qs_rol.filter(mouse=m, fedDate=d)
            if qs_rol_m_day.exists():
                roll_raw[d.isoformat()] = qs_rol_m_day[0]['rollMaxPokeAcc']
            else:
                roll_raw[d.isoformat()] = 'na'
        cri_max_rol_avg30_raw.append(roll_raw.copy())
        
        # max10_ralling_30 binary
        roll_raw['dataType'] = "max10_rolling_30_binary"
        roll_raw['threshold'] = cri_max_rol_avg30
        for dd in range(time_acq_range):
            d = pick_date_start + timedelta(days=dd+1)
            qs_rol_m_day = qs_rol.filter(mouse=m, fedDate=d).filter(rollMaxPokeAcc__gt = cri_max_rol_avg30)
            if qs_rol_m_day.exists():
                roll_raw[d.isoformat()] = 1
            else:
                roll_raw[d.isoformat()] = 0
        cri_max_rol_avg30_binary.append(roll_raw.copy())

        # cri_acq_result
        roll_raw['dataType'] = "acq_sum"
        roll_raw['threshold'] = ""
        roll_binary = roll_raw.copy()
        roll_binary['dataType'] = "acq_binary"
        for dd in range(time_acq_range):
            d = pick_date_start + timedelta(days=dd+1)

            roll_raw[d.isoformat()] = cri_num_p_day_binary[-1][d.isoformat()] + cri_stab_yes_binary[-1][d.isoformat()] + cri_end_day_acc_binary[-1][d.isoformat()] + cri_max_rol_avg30_binary[-1][d.isoformat()]
            roll_binary[d.isoformat()] = 1 if roll_raw[d.isoformat()] == 4 else 0
        cri_acq_sum.append(roll_raw.copy())
        cri_acq_binary.append(roll_binary.copy())


    # return
    return cri_acq_binary + cri_acq_sum + cri_num_p_day_binary + cri_stab_yes_binary + cri_end_day_acc_binary + cri_max_rol_avg30_binary + cri_end_day_acc_raw + cri_num_p_day_raw + cri_max_rol_avg30_raw
