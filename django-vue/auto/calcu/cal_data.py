from auto.models import Mouse, FedDataRaw, FedDataByHour, FedDataByDay, Cohort, FedDataRolling, FedDataTestType, FedDataByRT, FedDataRollingPoke
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Avg, F, RowRange, Window, Max, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.db.models import Count
import numpy as np
import copy
import math
import pytz

NUM_P_DAY=0
END_DAY_ACC=1
STAB_YES=2
MAX10_ROLLING_30=3
ACQ_TABLE=4
RT_AVG=5
RT_SEM=6
RT_PC=7
RT_RAW=8
ROLLING_POKE=9
MALE=0
FEMALE=1
DEBUG=1

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
        for fed_day in day_set: 
            if DEBUG: 
                print(m)
                print("cal_hr_day")
            cal_hr_day(m, fed_day)

            if DEBUG:
                print("cal_rolling_avg_nonwindow")
            cal_rolling_avg_nonwindow(m, fed_day)
            if DEBUG:
                print("cal_rolling_avg_nonwindow_cur_poke")
            cal_rolling_avg_nonwindow_cur_poke(m, fed_day)

            if DEBUG:
                print("cal_rolling_window")
            cal_rolling_window(m, fed_day, 30)
            if DEBUG:
                print("cal_rolling_window_cur_poke")
            cal_rolling_window_cur_poke(m, fed_day, 30)


def get_mouse_list(cohort_id):
    qs = Mouse.objects.filter(fed__cohort_id=cohort_id)
    return list(qs) 

def get_day_set(m):
    trans_from_caled_day = FedDataByDay.objects.filter(mouse=m)
    trans_from_raw = FedDataRaw.objects.filter(mouse=m).values('actNumDay').annotate(fedNumDay=Max("actNumDay"))

    trans_from_caled_day_set = set()
    for t in trans_from_caled_day:
        fed_day = t.fedNumDay
        trans_from_caled_day_set.add(fed_day)

    trans_from_raw_set = set()
    for t in trans_from_raw:
        fed_day = t['actNumDay']
        trans_from_raw_set.add(fed_day)

    return(trans_from_raw_set-trans_from_caled_day_set)

def cal_hr_day(m, fed_day):
    print(fed_day)
    qs = FedDataRaw.objects.filter(mouse=m, actNumDay=fed_day)
    # get active poke
    active_poke = qs[0].activePoke  
    if len(qs) < 2:
        print("WARNING: qs < 2")
        onset_timestamp = qs[0].actTimestamp # deal with only 1 transaction
    else:
        onset_timestamp = qs[1].actTimestamp # onset from the second transaction

    # for retrieval time
    rt_avg, rt_sem, rt_pel, rt_raw = cal_rt_of_day(m, fed_day, onset_timestamp)

    # for day and hr 
    total_l = 0
    total_r = 0
    total_p = 0
    for hr in range(8):
        qs_hr = qs.filter(actTimestamp__lte=(onset_timestamp+timedelta(hours=hr+1)), actTimestamp__gt=(onset_timestamp+timedelta(hours=hr)))
        # select pokes 
        qs_hr_poke = qs_hr.filter(event = 1)
        qs_hr_poke_left = 0
        qs_hr_poke_right = 0
        if qs_hr_poke and len(qs_hr_poke) > 1:
            rc_pre = -1
            for i in range(len(qs_hr_poke)):
                if i==0:
                    if qs_hr_poke[i].rightPokeCount == 1:
                        qs_hr_poke_right += 1
                    else:
                        qs_hr_poke_left += 1
                else:
                    if qs_hr_poke[i].rightPokeCount != rc_pre:
                        qs_hr_poke_right += 1
                    else:
                        qs_hr_poke_left += 1
                rc_pre = qs_hr_poke[i].rightPokeCount

        # select pellects
        qs_hr_pc = qs_hr.filter(event = 2 )

        cur_l = qs_hr_poke_left
        cur_r = qs_hr_poke_right
        cur_p = len(qs_hr_pc)
        total_l += cur_l
        total_r += cur_r
        total_p += cur_p

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

        print("before insert pokeAcc=%f cur_l %d curl_r %d p %d" % (poke_acc, cur_l, cur_r, cur_p))
        # insert into db
        fedhr = FedDataByHour(leftPokeCount=cur_l, rightPokeCount=cur_r, pelletCount=cur_p, activePoke=active_poke, pokeAcc=poke_acc, startTime=onset_timestamp+timedelta(hours=hr), endTime=onset_timestamp+timedelta(hours=hr+1), numHour=hr+1, fedDate=onset_timestamp.date(), fedNumDay=fed_day, mouse=m)
        fedhr.save()

        # insert into day table
        if hr == 7: 
            poke_acc=0;
            if (total_l+total_r) == 0:
                poke_acc=0;
            elif active_poke == 1: # left
                poke_acc = total_l / (total_l+total_r)
            elif active_poke == 2: #right
                poke_acc = total_r / (total_l+total_r)
            else:
                raise Exception("Invalid active_poke code.") 

            fedday = FedDataByDay(rtAvg=rt_avg, rtSem=rt_sem, rtPelletCount=rt_pel, rtRaw=rt_raw, leftPokeCount=total_l, rightPokeCount=total_r, pelletCount=total_p, activePoke=active_poke, pokeAcc=poke_acc, fedDate=onset_timestamp.date(), fedNumDay=fed_day, mouse=m)
            fedday.save()


# cal rolling avg of poke_acc
def cal_rolling_avg_nonwindow(m, fed_day):
    qs = FedDataRaw.objects.filter(mouse=m, actNumDay=fed_day)
    if len(qs) < 2:
        print("WARNING: qs < 2")
        return

    # get active poke
    active_poke = qs[0].activePoke  

    # get onset time
    total_qs = len(qs)
    onset_index = 16
    if onset_index >= total_qs:
        return
    for i in range(len(qs)):
        if onset_index+i >=len(qs): # can not find onset, return
            return

        if qs[onset_index+i].event == 2: # ignore pellet count record for onset
            continue
        else:
            onset_index = onset_index+i
            break

    onset_time = qs[onset_index].actTimestamp

    # ignore all pellet counts
    qs_poke = FedDataRaw.objects.filter(mouse=m, actNumDay=fed_day, event=1, actTimestamp__gte=onset_time)
    #print(len(qs_poke))

    #count qs_acc
    for i in range(len(qs_poke)):
        lc = qs_poke[i].leftPokeCount # TBD, have to remove pokeWithPellet
        rc = qs_poke[i].rightPokeCount # TBD, have to remove pokeWithPellet
        ts = qs_poke[i].actTimestamp

        # cal poke acc
        poke_acc=0;
        if lc+rc == 0:
            poke_acc=0;
        elif active_poke == 1: # left
            poke_acc = lc / (lc+rc)
        elif active_poke == 2: #right
            poke_acc = rc / (lc+rc)
        else:
            raise Exception("Invalid active_poke code.") 

        fdr = FedDataRolling(pokeAcc=poke_acc, windowSize=1, startTime=ts, endTime=ts, fedDate=ts.date(), fedNumDay=fed_day, mouse=m)
        fdr.save()

# cal rolling avg of cur poke
def cal_rolling_avg_nonwindow_cur_poke(m, fed_day):
    qs = FedDataRaw.objects.filter(mouse=m, actNumDay=fed_day)
    if len(qs) < 2:
        print("WARNING: qs < 2")
        return

    # ignore all pellet counts
    onset_time = qs[0].actTimestamp
    qs_poke = FedDataRaw.objects.filter(mouse=m, actNumDay=fed_day, event=1, actTimestamp__gte=onset_time) 

    if qs_poke and len(qs_poke) > 3: # at least 2 records # 3 should be 1?
        rc_pre = -1
        for i in range(len(qs_poke)):
            cur_poke = 1 # default = left poke
            ts = qs_poke[i].actTimestamp
            if i==0:
                if qs_poke[i].rightPokeCount == 1:
                    cur_poke = 0 # set 0 for right poke
                rc_pre = qs_poke[i].rightPokeCount
            else:
                if qs_poke[i].rightPokeCount != rc_pre: #right count increase #TBD: need to verify poke with pellets => evert=1 has already filtered out them
                    cur_poke = 0 # set 0 for right poke
                # update rc_pre
                rc_pre = qs_poke[i].rightPokeCount

            fdr = FedDataRollingPoke(curPoke=cur_poke, windowSize=1, startTime=ts, endTime=ts, fedDate=ts.date(), fedNumDay=fed_day, mouse=m)
            fdr.save()


# cal rolling avg of poke_acc
def cal_rolling_window(m, fed_day, win_size):
    #start rolling
    #https://stackoverflow.com/questions/48790322/fast-moving-average-computation-with-django-orm
    items = FedDataRolling.objects.filter(windowSize=1, mouse=m, fedNumDay=fed_day).annotate(
            avg=Window(
                expression=Avg('pokeAcc'), 
                order_by=F('id').asc(), 
                frame=RowRange(start=(0-win_size+1),end=0)
                )
            )

    #print(items[29].avg)
    for i in range(win_size-1, len(items)):
        avg = items[i].avg
        fdr = FedDataRolling(pokeAcc=avg, windowSize=win_size, startTime=items[i-(win_size-1)].startTime, endTime=items[i].startTime, fedDate=items[i].startTime.date(), fedNumDay=fed_day, mouse=m)
        fdr.save()


# cal rolling sum of cur poke: left
def cal_rolling_window_cur_poke(m, fed_day, win_size):
    #start rolling
    #https://stackoverflow.com/questions/48790322/fast-moving-average-computation-with-django-orm
    items = FedDataRollingPoke.objects.filter(windowSize=1, mouse=m, fedNumDay=fed_day).annotate(
        total_left_pokes=Window(
            expression=Sum('curPoke'), 
            order_by=F('id').asc(), 
            frame=RowRange(start=(0-win_size+1),end=0)
            )
        )
    for i in range(win_size-1, len(items)):
        if i == win_size-1: #skip the first poke (implement in excel)
            continue
        total_left_pokes = items[i].total_left_pokes
        fdrp = FedDataRollingPoke(curPoke=total_left_pokes, windowSize=win_size, startTime=items[i-(win_size-1)].startTime, endTime=items[i].startTime, fedDate=items[i].fedDate, fedNumDay=fed_day, mouse=m)
        fdrp.save()

def cal_acq(cohort_id, time_acq_picker, time_acq_range, cri_num_p_day_m, cri_num_p_day_f, cri_end_day_acc_m, cri_end_day_acc_f, cri_max_rol_avg30_m, cri_max_rol_avg30_f, cri_stab_yes_m, cri_stab_yes_f, cri_rt_thres_m, cri_rt_thres_f, cri_filter_test_type, cri_rol_poke_m, cri_rol_poke_f, cri_rol_poke_w_size ):
    # for rolling avg cum acc
    window_size = 30

    # get start, end num_day
    if time_acq_picker:
        d_str_sp = time_acq_picker.split('-')
        pick_date = date(year=int(d_str_sp[0]), month=int(d_str_sp[1]), day=int(d_str_sp[2]))
    else: 
        pick_date = date.today()

    pick_num_day_end = FedDataByDay.objects.filter(mouse__fed__cohort_id=cohort_id, fedDate=pick_date)
    if not pick_num_day_end:
        last_day = FedDataByDay.objects.filter(mouse__fed__cohort_id=cohort_id).order_by('fedNumDay').last()
        if last_day:
            pick_date = last_day.fedDate
            pick_num_day_end = last_day.fedNumDay
        else:
            return []
    else:
        pick_num_day_end = pick_num_day_end[0].fedNumDay

    pick_num_day_start = pick_num_day_end - (time_acq_range-1)
    if pick_num_day_start < 1:
        pick_num_day_start = 1
    pick_num_day_total = pick_num_day_end-pick_num_day_start+1

    if DEBUG: 
        print("DEBUG MSG: pick date ", pick_date)
        print("DEBUG MSG: pick_num_day_start", pick_num_day_start)
        print("DEBUG MSG: pick_num_day_end", pick_num_day_end)
        print("DEBUG MSG: pick total days", pick_num_day_total)

    # get mice list
    mice_list = Mouse.objects.select_related('fed').filter(fed__cohort_id=cohort_id).order_by('id')

    # get byday feddata
    feddata_cohort = FedDataByDay.objects.filter(mouse__fed__cohort_id=cohort_id, fedNumDay__gte=pick_num_day_start, fedNumDay__lte=pick_num_day_end)
    # get rolling acc day info, different structure
    feddata_cohort_rolling = FedDataRolling.objects.filter(mouse__fed__cohort_id=cohort_id, fedNumDay__gte=pick_num_day_start, fedNumDay__lte=pick_num_day_end, windowSize=window_size).values('fedNumDay', 'mouse_id').annotate(rollMaxPokeAcc=Max('pokeAcc')) # group by fedNumDay, mouse_id and max pokeAcc

    feddata_day_arr_name = get_feddate_array_name(feddata_cohort, pick_num_day_start, pick_num_day_end)
    # prepare datatype, threshold
    feddata_datatype = ['num_p_day', 'end_day_acc', 'stab_yesterday', 'max10_rolling_30', 'acq_table']
    feddata_threshold = [ [cri_num_p_day_m, cri_num_p_day_f] , [cri_end_day_acc_m, cri_end_day_acc_f], [cri_stab_yes_m, cri_stab_yes_f], [cri_max_rol_avg30_m, cri_max_rol_avg30_f], [len(feddata_datatype)-1, len(feddata_datatype)-1]]
    feddata_datatype_rt = ['rt_avg','rt_sem','rt_pellet_count','rt_raw']
    feddata_threshold_rt = [cri_rt_thres_m, cri_rt_thres_f]
    feddata_datatype_poke = ['rolling_left_poke_%d' % (cri_rol_poke_w_size), 'rolling_right_poke_%d' % (cri_rol_poke_w_size)]
    feddata_threshold_poke = [round(cri_rol_poke_m*cri_rol_poke_w_size), round(cri_rol_poke_f*cri_rol_poke_w_size)]

    # for each mouse
    mouse_data_list = []
    for mouse in mice_list:
        # generate mouse demo data, threshold 
        mouse_thres_index = -1
        mouse_data={}
        mouse_data['mouse_id'] = mouse.id
        mouse_data['mouse_name'] = mouse.mouseDisplayName
        mouse_data['fed'] = mouse.fed.fedDisplayName
        mouse_data['genotype'] = mouse.genotype
        if mouse.sex == 0:
            mouse_data['sex'] = 'na'
        elif mouse.sex == 1:
            mouse_data['sex'] = 'male'
            mouse_thres_index = MALE
        elif mouse.sex == 2:
            mouse_data['sex'] = 'female'
            mouse_thres_index = FEMALE
        else:
            mouse_data['sex'] = mouse.sex

        # loop each day, init raw and binary table
        thres_raw = [0] * (len(feddata_datatype)* (pick_num_day_total))
        thres_binary = [0] * (len(feddata_datatype)* (pick_num_day_total))
        # for rt raw data, init raw table
        thres_raw_rt = [0] * (len(feddata_datatype_rt)* (pick_num_day_total))
        # for roll_poke, init raw table
        thres_raw_poke = [0] * (len(feddata_datatype_poke)* (pick_num_day_total))

        if mouse_thres_index != -1: # either male or female

            has_shown_first_3R_PR_QU_X = 0
            has_shown_first_RE = 0
            has_shown_first_E = 0
            pre_day_avg_pokes = 0

            # for each day
            for feddata_num_day_index in range(pick_num_day_start, pick_num_day_end+1):

                feddata_num_day_offset = feddata_num_day_index-pick_num_day_start
    
                acq_table_count = 0
                # get byday feddata via filter
                feddata_mouse_day = feddata_cohort.filter(mouse=mouse, fedNumDay=feddata_num_day_index)
                if feddata_mouse_day:
                    # day filter for num_p_day
                    cur_day_count = feddata_mouse_day[0].pelletCount
                    cur_day_right_pokes = feddata_mouse_day[0].rightPokeCount
                    thres_raw[NUM_P_DAY*pick_num_day_total+feddata_num_day_offset] = cur_day_count
                    if cur_day_count >= feddata_threshold[NUM_P_DAY][mouse_thres_index]:
                        thres_binary[NUM_P_DAY*pick_num_day_total+feddata_num_day_offset] = 1
                        acq_table_count += 1

                    # get pre day count for stability

                    # set current day pellet count
                    thres_raw[STAB_YES*pick_num_day_total+feddata_num_day_offset] = cur_day_count

                    # default: compare previous day (FR1, FR3, 3R, 3R_PR/X, 3R_QU/X)
                    # feddata_num_day_offset=0 means the first day in range
                    if feddata_num_day_offset >= 0: 
                        pre_day_count = 0
                        # default
                        if feddata_num_day_offset == 0: # not in thres_raw but maybe in byday table
                            pre_day_from_cohort = FedDataByDay.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index-1)
                            if pre_day_from_cohort:
                                pre_day_count = pre_day_from_cohort[0].pelletCount 
                        else:
                            pre_day_count = thres_raw[NUM_P_DAY*pick_num_day_total+(feddata_num_day_offset-1)]

                        test_type_cur = FedDataTestType.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index)
                        test_type_pre = FedDataTestType.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index-1)
                        # check current test_type
                        # if cur=3R_QU/X, 3R_PR/X, skip pre
                        if test_type_cur and (
                                test_type_cur[0].testType == "3R_QU" or test_type_cur[0].testType == "3R_QU_X" 
                                or test_type_cur[0].testType == "3R_PR" or test_type_cur[0].testType == "3R_PR_X"
                                ) and has_shown_first_3R_PR_QU_X == 0:
                            # retrieve pre-pre day
                            prepre_day_from_cohort = FedDataByDay.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index-2)
                            if prepre_day_from_cohort:
                                pre_day_count = prepre_day_from_cohort[0].pelletCount
                            has_shown_first_3R_PR_QU_X = 1

                        # if cur=RE, looks for the last 3R_QU/X
                        elif test_type_cur and ( 
                                test_type_cur[0].testType == "RE"
                                ) and has_shown_first_RE == 0:
                            # retrieve the last 3R_QU/X
                            prepre_day_from_cohort = FedDataByDay.objects.raw('SELECT `auto_feddatabyday`.pelletCount, `auto_feddatabyday`.fedNumDay, `auto_feddatabyday`.mouse_id, `auto_feddatabyday`.id from `auto_feddatabyday` INNER JOIN `auto_feddatatesttype` ON `auto_feddatabyday`.mouse_id = `auto_feddatatesttype`.mouse_id AND `auto_feddatabyday`.fedNumDay = `auto_feddatatesttype`.fedNumDay WHERE (`auto_feddatatesttype`.testType = "3R_QU_X" OR `auto_feddatatesttype`.testType = "3R_QU") AND (`auto_feddatabyday`.mouse_id = %d) AND (`auto_feddatabyday`.fedNumDay < %d ) ORDER BY `auto_feddatabyday`.fedNumDay ' % (mouse.id, feddata_num_day_index) )
                            #for item in prepre_day_from_cohort:
                            #    print(item.__dict__)
                            if prepre_day_from_cohort:
                                pre_day_count = prepre_day_from_cohort[-1].pelletCount
                            has_shown_first_RE = 1

                        # if cur=E, avg the last 4 (3R_QU/X) 
                        elif test_type_cur and (
                                test_type_cur[0].testType == "E"
                                ) and has_shown_first_E == 0:
                            # get the last 4
                            prepre_day_from_cohort = FedDataByDay.objects.raw('SELECT MAX(`auto_feddatabyday`.rightPokeCount) as rightPokeCount, MAX(`auto_feddatabyday`.id) as id from `auto_feddatabyday` INNER JOIN `auto_feddatatesttype` ON `auto_feddatabyday`.mouse_id = `auto_feddatatesttype`.mouse_id AND `auto_feddatabyday`.fedNumDay = `auto_feddatatesttype`.fedNumDay WHERE (`auto_feddatatesttype`.testType = "3R_QU_X" OR `auto_feddatatesttype`.testType = "3R_QU") AND (`auto_feddatabyday`.mouse_id = %d) AND (`auto_feddatabyday`.fedNumDay < %d ) GROUP BY `auto_feddatabyday`.fedNumDay, `auto_feddatabyday`.mouse_id ORDER BY `auto_feddatabyday`.fedNumDay DESC LIMIT 4' % (mouse.id, feddata_num_day_index) )
                            #for item in prepre_day_from_cohort:
                            #    print(item.__dict__)
                            # average
                            if prepre_day_from_cohort:
                                count=0
                                pre_day_avg_pokes=0
                                for item in prepre_day_from_cohort:
                                    pre_day_avg_pokes += item.rightPokeCount 
                                    count += 1
                                pre_day_avg_pokes = pre_day_avg_pokes / count # right pokes
                                #print(pre_day_avg_pokes)
                            has_shown_first_E = 1

                        # if pre=QU/X, PR/X, skip pre
                        elif test_type_pre and (
                                test_type_pre[0].testType == "QU" or test_type_pre[0].testType == "QU_X" 
                                or test_type_pre[0].testType == "PR" or test_type_pre[0].testType == "PR_X"
                                ):
                            # retrieve pre-pre day
                            prepre_day_from_cohort = FedDataByDay.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index-2)
                            if prepre_day_from_cohort:
                                pre_day_count = prepre_day_from_cohort[0].pelletCount
                        
                        # calculate max/min threshold
                        if test_type_cur and (
                            test_type_cur[0].testType == "E" 
                            ) and has_shown_first_E == 1:
                            max_pre_day_pokes = pre_day_avg_pokes*feddata_threshold[STAB_YES][mouse_thres_index]
                            min_pre_day_pokes = 0
                            thres_raw[STAB_YES*pick_num_day_total+feddata_num_day_offset] = "%d(%d-%d)" % (cur_day_right_pokes, max_pre_day_pokes, min_pre_day_pokes)
                            # default E value = 0
                            thres_binary[STAB_YES*pick_num_day_total+feddata_num_day_offset] = 0
                            if cur_day_right_pokes <= max_pre_day_pokes: 
                                thres_binary[STAB_YES*pick_num_day_total+feddata_num_day_offset] = 'E'
                        else:
                            max_pre_day_count = pre_day_count + pre_day_count*feddata_threshold[STAB_YES][mouse_thres_index]
                            min_pre_day_count = pre_day_count - pre_day_count*feddata_threshold[STAB_YES][mouse_thres_index]
                            thres_raw[STAB_YES*pick_num_day_total+feddata_num_day_offset] = "%d(%d-%d)" % (cur_day_count, max_pre_day_count, min_pre_day_count)
                            if cur_day_count >= min_pre_day_count and cur_day_count <= max_pre_day_count:
                                thres_binary[STAB_YES*pick_num_day_total+feddata_num_day_offset] = 1
                                acq_table_count += 1

                    # handle end day acc
                    cur_day_poke_acc = feddata_mouse_day[0].pokeAcc
                    thres_raw[END_DAY_ACC*pick_num_day_total+feddata_num_day_offset] = float(cur_day_poke_acc)
                    if cur_day_poke_acc > feddata_threshold[END_DAY_ACC][mouse_thres_index]:
                        thres_binary[END_DAY_ACC*pick_num_day_total+feddata_num_day_offset] = 1
                        acq_table_count += 1

                    # handle retrieval time RT 
                    cur_day_rt_avg = feddata_mouse_day[0].rtAvg
                    cur_day_rt_sem = feddata_mouse_day[0].rtSem
                    cur_day_rt_pc = feddata_mouse_day[0].rtPelletCount
                    cur_day_rt_raw = feddata_mouse_day[0].rtRaw
                    # if thres != 0, recalculate the stat values
                    if feddata_threshold_rt[mouse_thres_index] != 0:
                        # re-calculate avg
                        if cur_day_rt_raw:
                            rt_list = cur_day_rt_raw.split(",")
                            rt_np_arr = np.array(rt_list)
                            rt_np_arr = rt_np_arr.astype(int)
                            # filter out 
                            rt_np_arr_filtered = rt_np_arr[ (rt_np_arr < feddata_threshold_rt[mouse_thres_index]) ] 

                            if len(rt_np_arr_filtered) != 0: 
                                if len(rt_np_arr_filtered) == 1:
                                    cur_day_rt_sem = 0
                                else:
                                    cur_day_rt_sem = round(np.std(rt_np_arr_filtered, ddof=1) / np.sqrt(np.size(rt_np_arr_filtered)), 4)
                                cur_day_rt_avg = round(np.mean(rt_np_arr_filtered), 4)
                                cur_day_rt_raw = ",".join(str(v) for v in rt_np_arr_filtered.tolist())
                                cur_day_rt_pc = rt_np_arr_filtered.size 

                            else:
                                cur_day_rt_sem = 0
                                cur_day_rt_avg = 0
                                cur_day_rt_raw = ""
                                cur_day_rt_pc = 0

                        else:
                            cur_day_rt_sem = 0
                            cur_day_rt_avg = 0
                            cur_day_rt_raw = ""
                            cur_day_rt_pc = 0

                    # fill into thres_raw_rt
                    thres_raw_rt[0*pick_num_day_total+feddata_num_day_offset] = cur_day_rt_avg
                    thres_raw_rt[1*pick_num_day_total+feddata_num_day_offset] = cur_day_rt_sem
                    thres_raw_rt[2*pick_num_day_total+feddata_num_day_offset] = cur_day_rt_pc
                    thres_raw_rt[3*pick_num_day_total+feddata_num_day_offset] = cur_day_rt_raw


                # get rolling filter (CumAcc)
                feddata_rolling_mouse_day = feddata_cohort_rolling.filter(mouse=mouse, fedNumDay=feddata_num_day_index) 
                if feddata_rolling_mouse_day:
                    roll_max_poke_acc = feddata_rolling_mouse_day[0]['rollMaxPokeAcc']
                    thres_raw[MAX10_ROLLING_30*pick_num_day_total+feddata_num_day_offset] = float(roll_max_poke_acc)
                    if roll_max_poke_acc > feddata_threshold[MAX10_ROLLING_30][mouse_thres_index]:
                        thres_binary[MAX10_ROLLING_30*pick_num_day_total+feddata_num_day_offset] = 1
                        acq_table_count += 1

                # get rolling poke (left and right)
                feddata_cohort_rolling_poke = FedDataRollingPoke.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index, windowSize=cri_rol_poke_w_size)
                if not feddata_cohort_rolling_poke:
                    cal_rolling_window_cur_poke(mouse,feddata_num_day_index,cri_rol_poke_w_size)

                feddata_cohort_rolling_poke = FedDataRollingPoke.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index, windowSize=cri_rol_poke_w_size)
                if feddata_cohort_rolling_poke:
                    # check left poke
                    feddata_cohort_rolling_poke_left = feddata_cohort_rolling_poke.filter(curPoke__gte = feddata_threshold_poke[mouse_thres_index])
                    if feddata_cohort_rolling_poke_left:
                        duration = feddata_cohort_rolling_poke_left[0].endTime - feddata_cohort_rolling_poke[0].startTime
                        total_seconds = int(duration.total_seconds())
                        # select sum of left pokes
                        feddata_cohort_rolling_poke_left_agg = FedDataRollingPoke.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index, windowSize=1, endTime__lte = feddata_cohort_rolling_poke_left[0].endTime).aggregate(left_pokes = Sum("curPoke"), total_pokes = Count("curPoke"))
                        if feddata_cohort_rolling_poke_left_agg:
                            left_pokes = feddata_cohort_rolling_poke_left_agg['left_pokes']  
                            total_pokes = feddata_cohort_rolling_poke_left_agg['total_pokes']
                            thres_raw_poke[0*pick_num_day_total+feddata_num_day_offset] = "%02d:%02d:%02d,%s,%d,%d" % (total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60, feddata_cohort_rolling_poke_left[0].endTime.astimezone(pytz.timezone('Etc/GMT+4')), left_pokes -1, total_pokes - left_pokes -1 )
                        else:
                            raise Exception("feddata_cohort_rolling_poke_left_agg can not be null")

                    # check right poke
                    #(window - curPoke) >= thres (right)
                    #-curPoke >= thres - window
                    #curPoke <= window - thres
                    feddata_cohort_rolling_poke_right = feddata_cohort_rolling_poke.filter(curPoke__lte = (cri_rol_poke_w_size - feddata_threshold_poke[mouse_thres_index]) )
                    if feddata_cohort_rolling_poke_right:
                        duration = feddata_cohort_rolling_poke_right[0].endTime - feddata_cohort_rolling_poke[0].startTime
                        total_seconds = int(duration.total_seconds())
                        # select sum of left pokes
                        feddata_cohort_rolling_poke_right_agg = FedDataRollingPoke.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index, windowSize=1, endTime__lte = feddata_cohort_rolling_poke_right[0].endTime).aggregate(left_pokes = Sum("curPoke"), total_pokes = Count("curPoke"))
                        if feddata_cohort_rolling_poke_right_agg:
                            left_pokes = feddata_cohort_rolling_poke_right_agg['left_pokes'] 
                            total_pokes = feddata_cohort_rolling_poke_right_agg['total_pokes'] 
                            thres_raw_poke[1*pick_num_day_total+feddata_num_day_offset] = "%02d:%02d:%02d,%s,%d,%d" % (total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60, feddata_cohort_rolling_poke_right[0].endTime.astimezone(pytz.timezone('Etc/GMT+4')), left_pokes -1, total_pokes - left_pokes -1 )
                        else:
                            raise Exception("feddata_cohort_rolling_poke_right_agg can not be null")

                # get final acq
                thres_raw[ACQ_TABLE*pick_num_day_total+feddata_num_day_offset] = acq_table_count
                if acq_table_count == feddata_threshold[ACQ_TABLE][mouse_thres_index]:
                    thres_binary[ACQ_TABLE*pick_num_day_total+feddata_num_day_offset] = 1
                elif thres_binary[STAB_YES*pick_num_day_total+feddata_num_day_offset] == 'E':
                    thres_binary[ACQ_TABLE*pick_num_day_total+feddata_num_day_offset] = 'E'


        if DEBUG:
            print(thres_raw)
            print(thres_binary)

        # thres_raw, binary ready
        mouse_data['thres_raw'] = thres_raw
        mouse_data['thres_binary'] = thres_binary
        mouse_data['thres_raw_rt'] = thres_raw_rt
        mouse_data['thres_raw_poke'] = thres_raw_poke

        # append mouse data
        mouse_data_list.append(mouse_data)

    print("between formatting")
    ### formating output ###
    final_acq_output_tabs = {}
    final_acq_output_tabs_filtered = {}
    final_metadata = {}
    for tab_index in range(4):
        final_acq_output_tabs[tab_index] = []
        final_acq_output_tabs_filtered[tab_index] = []
    final_metadata[0] = []
    # get test type list and max filter count of each mouse
    test_type_list = {}
    filter_count_list = []
    is_retest = 0
    for mouse in mouse_data_list:
        test_type_list[mouse['mouse_id']] = {}
        mouse_row_filter_count = 0
        for day_offset in range(pick_num_day_total):
            test_type = FedDataTestType.objects.filter(mouse_id=mouse['mouse_id'], fedNumDay=pick_num_day_start+day_offset)
            if test_type:
                test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_offset]] = test_type[0].testType
                if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_offset]] == cri_filter_test_type:
                    mouse_row_filter_count += 1
                elif test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_offset]] == cri_filter_test_type+"_X":
                    mouse_row_filter_count += 1
                    is_retest = 1
            else:
                test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_offset]] = ""
        filter_count_list.append(mouse_row_filter_count)

    # generate the ACQ_TABLE - RT_RAW tables
    for type_index in [ACQ_TABLE, NUM_P_DAY, STAB_YES, END_DAY_ACC, MAX10_ROLLING_30, RT_AVG, RT_SEM, RT_PC, RT_RAW, ROLLING_POKE]:
        for mouse in mouse_data_list:
            mouse_row = {}
            mouse_row['mouse_id'] = mouse['mouse_id']
            mouse_row['mouse_name'] = mouse['mouse_name']
            mouse_row['fed'] = mouse['fed']
            mouse_row['genotype'] = mouse['genotype']
            mouse_row['sex'] = mouse['sex']
            # for test type filter
            mouse_row_filter = copy.deepcopy(mouse_row)

            if type_index < RT_AVG:
                mouse_row['data_type'] = feddata_datatype[type_index]
                mouse_row_filter['data_type'] = feddata_datatype[type_index]
                # binary
                mouse_row_filter_count = 0
                for day_index in range(pick_num_day_total):
                    # for FF rule
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF' and type_index != NUM_P_DAY and type_index != STAB_YES:
                        mouse_row[feddata_day_arr_name[day_index]] = ''
                    else:
                        mouse_row[feddata_day_arr_name[day_index]] = mouse['thres_binary'][type_index*pick_num_day_total + day_index]
                    # if meet filter condition
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type or test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type+"_X":
                        # for FF rule
                        if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF' and type_index != NUM_P_DAY and type_index != STAB_YES:
                            mouse_row_filter['s_align'+str(mouse_row_filter_count+1)] = ''
                        else:
                            mouse_row_filter['s_align'+str(mouse_row_filter_count+1)] = mouse['thres_binary'][type_index*pick_num_day_total + day_index]
                        mouse_row_filter_count += 1
                # fill missing col
                max_filter_count = max(filter_count_list)
                if mouse_row_filter_count > 0 and mouse_row_filter_count != max_filter_count:
                    # E.g. max_filter_count=5 mouse_row_filter_count=1
                    for miss_idx in range(mouse_row_filter_count, (max_filter_count-mouse_row_filter_count)+1 ):
                        mouse_row_filter['s_align'+str(miss_idx+1)] = ''
                # reset filter count for raw
                mouse_row_filter_count = 0
                # raw
                mouse_row['threshold'] = "M:%.2f F:%.2f" % (feddata_threshold[type_index][MALE], feddata_threshold[type_index][FEMALE])
                mouse_row_filter['threshold'] = "M:%.2f F:%.2f" % (feddata_threshold[type_index][MALE], feddata_threshold[type_index][FEMALE])
                for day_index in range(pick_num_day_total):
                    # for FF rule
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF' and type_index != NUM_P_DAY and type_index != STAB_YES:
                        mouse_row[feddata_day_arr_name[day_index]+" "] = ''
                    else:
                        mouse_row[feddata_day_arr_name[day_index]+" "] = mouse['thres_raw'][type_index*pick_num_day_total + day_index]
                    # if meet filter condition
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type or test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type+"_X":
                        # for FF rule
                        if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF' and type_index != NUM_P_DAY and type_index != STAB_YES:
                            mouse_row_filter['x_align'+str(mouse_row_filter_count+1)+" "] = ''
                        else:
                            mouse_row_filter['x_align'+str(mouse_row_filter_count+1)+" "] = mouse['thres_raw'][type_index*pick_num_day_total + day_index]
                        mouse_row_filter_count += 1
                # fill missing col
                max_filter_count = max(filter_count_list)
                if mouse_row_filter_count > 0 and mouse_row_filter_count != max_filter_count:
                    # E.g. max_filter_count=5 mouse_row_filter_count=1
                    for miss_idx in range(mouse_row_filter_count, (max_filter_count-mouse_row_filter_count)+1 ):
                        mouse_row_filter['x_align'+str(miss_idx+1)+" "] = ''

                # insert tabs array
                if type_index == ACQ_TABLE:
                    final_acq_output_tabs[0].append(mouse_row)
                    if mouse_row_filter_count != 0:
                        final_acq_output_tabs_filtered[0].append(mouse_row_filter)
                else:
                    final_acq_output_tabs[1].append(mouse_row)
                    if mouse_row_filter_count != 0:
                        final_acq_output_tabs_filtered[1].append(mouse_row_filter)

            elif type_index >= RT_AVG and type_index <= RT_RAW: # for rt
                type_index_rt = type_index-len(feddata_datatype)
                mouse_row['data_type'] = feddata_datatype_rt[ type_index_rt ]
                mouse_row_filter['data_type'] = feddata_datatype_rt[ type_index_rt ]
                mouse_row['threshold'] = "M:%.2f F:%.2f" % (feddata_threshold_rt[MALE], feddata_threshold_rt[FEMALE])
                mouse_row_filter['threshold'] = "M:%.2f F:%.2f" % (feddata_threshold_rt[MALE], feddata_threshold_rt[FEMALE])

                mouse_row_filter_count = 0
                for day_index in range(pick_num_day_total):
                    mouse_row[feddata_day_arr_name[day_index]+" "] = mouse['thres_raw_rt'][ type_index_rt*pick_num_day_total + day_index]
                    # filter test type
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type or test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type+"_X":
                        mouse_row_filter['s_align'+str(mouse_row_filter_count+1)+""] = mouse['thres_raw_rt'][ type_index_rt*pick_num_day_total + day_index]
                        mouse_row_filter_count += 1
                # fill missing col
                max_filter_count = max(filter_count_list)
                if mouse_row_filter_count > 0 and mouse_row_filter_count != max_filter_count:
                    for miss_idx in range(mouse_row_filter_count, (max_filter_count-mouse_row_filter_count)+1 ):
                        mouse_row_filter['s_align'+str(miss_idx+1)+""] = ''

                final_acq_output_tabs[2].append(mouse_row)
                if mouse_row_filter_count != 0:
                    final_acq_output_tabs_filtered[2].append(mouse_row_filter)
            elif type_index == ROLLING_POKE:
                # left poke
                mouse_row['data_type'] = feddata_datatype_poke[0]
                mouse_row_filter['data_type'] = feddata_datatype_poke[0]
                mouse_row['threshold'] = "M:%.2f F:%.2f" % (cri_rol_poke_m, cri_rol_poke_f)
                mouse_row_filter['threshold'] = "M:%.2f F:%.2f" % (cri_rol_poke_m, cri_rol_poke_f)

                mouse_row_filter_count = 0
                for day_index in range(pick_num_day_total):
                    # for FF rule
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF':
                        mouse_row[feddata_day_arr_name[day_index]+" "] = ''
                    else:
                        mouse_row[feddata_day_arr_name[day_index]+" "] = mouse['thres_raw_poke'][ 0*pick_num_day_total + day_index] # 0 for left poke data
                    # filter test type
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type or test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type+"_X":
                        # for FF rule
                        if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF':
                            mouse_row_filter['s_align'+str(mouse_row_filter_count+1)] = ''
                        else:
                            mouse_row_filter['s_align'+str(mouse_row_filter_count+1)] = mouse['thres_raw_poke'][ 0*pick_num_day_total + day_index]
                        mouse_row_filter_count += 1
                # fill missing col
                max_filter_count = max(filter_count_list)
                if mouse_row_filter_count > 0 and mouse_row_filter_count != max_filter_count:
                    for miss_idx in range(mouse_row_filter_count, (max_filter_count-mouse_row_filter_count)+1 ):
                        mouse_row_filter['s_align'+str(miss_idx+1)+''] = ''
                
                final_acq_output_tabs[2].append(mouse_row)
                if mouse_row_filter_count != 0:
                    final_acq_output_tabs_filtered[2].append(mouse_row_filter)

                # dup row for right poke
                mouse_row_right = copy.deepcopy(mouse_row)
                mouse_row_right_filter = copy.deepcopy(mouse_row_filter)
                # right poke
                mouse_row_right['data_type'] = feddata_datatype_poke[1]
                mouse_row_right_filter['data_type'] = feddata_datatype_poke[1]

                mouse_row_filter_count = 0
                for day_index in range(pick_num_day_total):
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF':
                        mouse_row_right[feddata_day_arr_name[day_index]+" "] = ''
                    else:
                        mouse_row_right[feddata_day_arr_name[day_index]+" "] = mouse['thres_raw_poke'][ 1*pick_num_day_total + day_index] # 1 for right poke data
                    # filter test type
                    if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type or test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == cri_filter_test_type+"_X":
                        if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_index]] == 'FF':
                            mouse_row_right_filter['s_align'+str(mouse_row_filter_count+1)] = ''
                        else:
                            mouse_row_right_filter['s_align'+str(mouse_row_filter_count+1)] = mouse['thres_raw_poke'][ 1*pick_num_day_total + day_index]
                        mouse_row_filter_count += 1
                # fill missing col
                max_filter_count = max(filter_count_list)
                if mouse_row_filter_count > 0 and mouse_row_filter_count != max_filter_count:
                    for miss_idx in range(mouse_row_filter_count, (max_filter_count-mouse_row_filter_count)+1 ):
                        mouse_row_right_filter['s_align'+str(miss_idx+1)+''] = ''

                final_acq_output_tabs[2].append(mouse_row_right)
                if mouse_row_filter_count != 0:
                    final_acq_output_tabs_filtered[2].append(mouse_row_right_filter)

    
    # generate test_type and date
    for mouse in mouse_data_list:
        mouse_row = {}
        mouse_row['mouse_id'] = mouse['mouse_id']
        mouse_row['mouse_name'] = mouse['mouse_name']
        mouse_row['fed'] = mouse['fed']
        mouse_row['genotype'] = mouse['genotype']
        mouse_row['sex'] = mouse['sex']
        # for date
        mouse_row_filter = copy.deepcopy(mouse_row)

        mouse_row['data_type'] = "test_type"
        mouse_row_filter['data_type'] = "date"
        mouse_row_filter['threshold'] = "M:%.2f F:%.2f" % (feddata_threshold_rt[MALE], feddata_threshold_rt[FEMALE])
        mouse_row_filter_count = 0
        for day_offset in range(pick_num_day_total):
            test_type = FedDataTestType.objects.filter(mouse_id=mouse['mouse_id'], fedNumDay=pick_num_day_start+day_offset)
            if test_type:
                mouse_row[feddata_day_arr_name[day_offset]] = test_type[0].testType
            else:
                mouse_row[feddata_day_arr_name[day_offset]] = ""
            # date info for filter
            if test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_offset]] == cri_filter_test_type or test_type_list[mouse['mouse_id']][feddata_day_arr_name[day_offset]] == cri_filter_test_type+"_X":
                mouse_row_filter['s_align'+str(mouse_row_filter_count+1)] = feddata_day_arr_name[day_offset]
                mouse_row_filter_count += 1
        # fill missing col
        max_filter_count = max(filter_count_list)
        if mouse_row_filter_count > 0 and mouse_row_filter_count != max_filter_count:
            for miss_idx in range(mouse_row_filter_count, (max_filter_count-mouse_row_filter_count)+1 ):
                mouse_row_filter['s_align'+str(miss_idx+1)+''] = ''

        final_acq_output_tabs[0].append(mouse_row)
        final_acq_output_tabs[1].append(mouse_row)
        if mouse_row_filter_count != 0:
            final_acq_output_tabs_filtered[0].append(mouse_row_filter)
            final_acq_output_tabs_filtered[1].append(mouse_row_filter)
            final_acq_output_tabs_filtered[2].append(mouse_row_filter)

    # prepare metadata table
    meta = {}
    meta['filtered_test_type_contains_retest_X'] = is_retest
    final_metadata[0].append(meta)

    return [final_acq_output_tabs, final_acq_output_tabs_filtered, final_metadata]

def get_feddate_array_name(feddata_day, pick_num_day_start, pick_num_day_end):
    # get feddate array name
    feddate_day_arr_name = []
    for pick_num_day in range(pick_num_day_start, pick_num_day_end+1):
        picked_day = feddata_day.filter(fedNumDay=pick_num_day)
        if picked_day:
            feddate_day_arr_name.append("d%d %s" % (pick_num_day, picked_day[0].fedDate.isoformat() ))
        else:
            feddate_day_arr_name.append("d%d" % (pick_num_day))
    return feddate_day_arr_name

def get_cohort_list_fun(study_id):
    output = []
    co = Cohort.objects.filter(study_id=study_id)
    if co:
        for item in co:
            one_co = {}
            one_co['cohort_id'] = item.id
            one_co['cohort_name'] = item.cohortDisplayName
            one_co['cohort_desc'] = item.cohortDesc
            output.append( one_co )

    return output

def put_new_cohort_fun(cohort_name):
    c = Cohort(cohortDisplayName=cohort_name, cohortDesc='', study_id=1, startDate='2022-03-05', endDate='2022-11-24' )
    c.save()

    return []

def del_cohort_fun(cohort_name):
    Cohort.objects.filter(cohortDisplayName=cohort_name).delete()
    return []


def get_mouse_list_fun(cohort_id):
    output_mouse_list = []
    mouses = Mouse.objects.select_related('fed').filter(fed__cohort_id = cohort_id)
    if mouses:
        for mouse in mouses:
            one_mouse = {}
            one_mouse['mouse_id'] = mouse.id
            one_mouse['mouse_name'] = mouse.mouseDisplayName
            one_mouse['mouse_genotype'] = mouse.genotype
            one_mouse['mouse_sex'] = mouse.sex
            one_mouse['mouse_FED'] = mouse.fed.fedDisplayName
            one_mouse['mouse_FED_day'] = ""
            # select uploaded days in this mouse
            fedNumDays = FedDataRaw.objects.filter(mouse=mouse).values('actNumDay').annotate(dcount=Count('actNumDay')).order_by('actNumDay')
            if fedNumDays:
                for fedNumDay in fedNumDays:
                    one_mouse['mouse_FED_day'] += str(fedNumDay['actNumDay']) + ","

            output_mouse_list.append(one_mouse)
    return output_mouse_list

def put_mouse_list_fun(mouse_list):
    for mouse in mouse_list:
        # update each mouse
        mouse_obj = Mouse.objects.filter(id=mouse['mouse_id'])
        mouse_inst = get_object_or_404(mouse_obj)
        mouse_inst.mouseDisplayName = mouse['mouse_name']
        mouse_inst.genotype = mouse['mouse_genotype']
        mouse_inst.sex = mouse['mouse_sex']
        mouse_inst.save()

    return []

def del_mouse_data_fun(mouse_data):
    # {'cohort_id': 7, 'del_mouse_id': '81', 'del_start_day': '30', 'del_end_day': '35'}
    del_mouse_id = int(mouse_data['del_mouse_id'])
    del_start_day = int(mouse_data['del_start_day'])
    del_end_day = int(mouse_data['del_end_day'])
    #print(mouse_data)

    # remove test type
    FedDataTestType.objects.filter(mouse_id=del_mouse_id, fedNumDay__gte = del_start_day, fedNumDay__lte = del_end_day).delete()
    # remove rolling, byhour, byday
    FedDataRolling.objects.filter(mouse_id=del_mouse_id, fedNumDay__gte = del_start_day, fedNumDay__lte = del_end_day).delete()
    FedDataRollingPoke.objects.filter(mouse_id=del_mouse_id, fedNumDay__gte = del_start_day, fedNumDay__lte = del_end_day).delete()
    FedDataByHour.objects.filter(mouse_id=del_mouse_id, fedNumDay__gte = del_start_day, fedNumDay__lte = del_end_day).delete()
    FedDataByDay.objects.filter(mouse_id=del_mouse_id, fedNumDay__gte = del_start_day, fedNumDay__lte = del_end_day).delete()
    # remove RT
    FedDataByRT.objects.filter(mouse_id=del_mouse_id, fedNumDay__gte = del_start_day, fedNumDay__lte = del_end_day).delete()
    # remove raw
    FedDataRaw.objects.filter(mouse_id=del_mouse_id, actNumDay__gte = del_start_day, actNumDay__lte = del_end_day).delete()

    return

# Given one mouse, one day, select all RT records and put into feddatabyrt
def cal_rt_of_day(m, fed_day, onset_timestamp):
    # check test type, decide the experiment time
    cut_off_hr=8
    qs_testtype = FedDataTestType.objects.filter(mouse=m, fedNumDay=fed_day)
    if qs_testtype:
        if qs_testtype[0].testType in ['QU', 'QU_X', 'E']:
            cut_off_hr=4

    qs_hr_rt = FedDataRaw.objects.filter(mouse=m, actNumDay=fed_day).filter(actTimestamp__lte=(onset_timestamp+timedelta(hours=cut_off_hr))).exclude(retrievalTime=-1)

    rt_list = []
    rt_pel = 0
    rt_pc_pre = 0
    for i_q in range(len(qs_hr_rt)):
        # insert into rt table
        feddayrt = FedDataByRT(actTimestamp=qs_hr_rt[i_q].actTimestamp, retrievalTime=qs_hr_rt[i_q].retrievalTime, pelletCount=qs_hr_rt[i_q].pelletCount, fedDate=qs_hr_rt[i_q].actTimestamp.date(), fedNumDay=fed_day, mouse=m)
        feddayrt.save()

        # deal with nan value pellet retrieval
        if qs_hr_rt[i_q].pelletCount - rt_pc_pre != 1: # miss nan, fill with 0
            rt_list.append(0)

        rt_list.append( qs_hr_rt[i_q].retrievalTime )
        rt_pel = qs_hr_rt[i_q].pelletCount

        rt_pc_pre = qs_hr_rt[i_q].pelletCount
    # mean and sem 
    rt_np_arr = np.array(rt_list)
    rt_sem = round(np.std(rt_np_arr, ddof=1) / np.sqrt(np.size(rt_np_arr)), 4)
    if math.isnan(rt_sem):
        rt_sem = 0
    rt_avg = round(np.mean(rt_np_arr), 4)
    if math.isnan(rt_avg):
        rt_avg = 0
    rt_raw = ",".join(str(v) for v in rt_list)

    return rt_avg, rt_sem, rt_pel, rt_raw
