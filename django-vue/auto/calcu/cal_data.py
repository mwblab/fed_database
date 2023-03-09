from auto.models import Mouse, FedDataRaw, FedDataByHour, FedDataByDay, Cohort, FedDataRolling, FedDataTestType
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Avg, F, RowRange, Window, Max
from django.db.models.functions import TruncDate

NUM_P_DAY=0
END_DAY_ACC=1
STAB_YES=2
MAX10_ROLLING_30=3
ACQ_TABLE=4
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
        for d_str in day_set: 
            d_str_sp = d_str.split('-')
            d = date(year=int(d_str_sp[2]), month=int(d_str_sp[0]), day=int(d_str_sp[1]))
            if DEBUG: 
                print(m)
                print(d)
                print("cal_hr_day")
            cal_hr_day(m, d)
            if DEBUG:
                print("cal_rolling_1")
            cal_rolling_avg(m, d)
            if DEBUG:
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
    fedNumDay = qs[0].actNumDay
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
        fedhr = FedDataByHour(leftPokeCount=cur_l, rightPokeCount=cur_r, pelletCount=cur_p, activePoke=active_poke, pokeAcc=poke_acc, startTime=onset_timestamp+timedelta(hours=hr), endTime=onset_timestamp+timedelta(hours=hr+1), numHour=hr+1, fedDate=d, fedNumDay=fedNumDay, mouse=m)
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

            fedday = FedDataByDay(leftPokeCount=qs_hr_last.leftPokeCount, rightPokeCount=qs_hr_last.rightPokeCount, pelletCount=qs_hr_last.pelletCount, activePoke=active_poke, pokeAcc=poke_acc, fedDate=d, fedNumDay=fedNumDay, mouse=m)
            fedday.save()

def cal_rolling_avg(m, d):
    qs = FedDataRaw.objects.filter(mouse=m, actTimestamp__date=d)

    # get active poke
    active_poke = qs[0].activePoke  
    fedNumDay = qs[0].actNumDay

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

        fdr = FedDataRolling(pokeAcc=poke_acc, windowSize=1, startTime=ts, endTime=ts, fedDate=d, fedNumDay=fedNumDay, mouse=m)
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
        fdr = FedDataRolling(pokeAcc=avg, windowSize=win_size, startTime=items[i-(win_size-1)].startTime, endTime=items[i].startTime, fedDate=d, fedNumDay=items[i].fedNumDay, mouse=m)
        fdr.save()

def cal_acq(cohort_id, time_acq_picker, time_acq_range, cri_num_p_day_m, cri_num_p_day_f, cri_end_day_acc_m, cri_end_day_acc_f, cri_max_rol_avg30_m, cri_max_rol_avg30_f, cri_stab_yes_m, cri_stab_yes_f):
    window_size = 30

    # get start, end num_day
    if time_acq_picker:
        d_str_sp = time_acq_picker.split('-')
        pick_date = date(year=int(d_str_sp[0]), month=int(d_str_sp[1]), day=int(d_str_sp[2]))
    else: 
        pick_date = date.today()

    pick_num_day_end = FedDataByDay.objects.filter(mouse__fed__cohort_id=cohort_id, fedDate=pick_date)
    if not pick_num_day_end:
        last_day = FedDataByDay.objects.filter(mouse__fed__cohort_id=cohort_id).order_by('fedDate').last()
        pick_date = last_day.fedDate
        pick_num_day_end = last_day.fedNumDay
    else:
        pick_num_day_end = pick_num_day_end[0].fedNumDay

    pick_num_day_start = pick_num_day_end - (time_acq_range-1)
    if pick_num_day_start < 1:
        pick_num_day_start = 1
    pick_num_day_total = pick_num_day_end-pick_num_day_start+1

    # get mice list
    mice_list = Mouse.objects.select_related('fed').filter(fed__cohort_id=cohort_id).order_by('id')

    # get day
    feddata_cohort = FedDataByDay.objects.filter(mouse__fed__cohort_id=cohort_id, fedNumDay__gte=pick_num_day_start, fedNumDay__lte=pick_num_day_end)
    # get rolling day info, different structure
    feddata_cohort_rolling = FedDataRolling.objects.filter(mouse__fed__cohort_id=cohort_id, fedNumDay__gte=pick_num_day_start, fedNumDay__lte=pick_num_day_end, windowSize=window_size).values('fedDate', 'fedNumDay', 'mouse_id').annotate(rollMaxPokeAcc=Max('pokeAcc'))

    feddata_day_arr_name = get_feddate_array_name(feddata_cohort, pick_num_day_start, pick_num_day_end)
    # prepare datatype, threshold
    feddata_datatype = ['num_p_day', 'end_day_acc', 'stab_yesterday', 'max10_rolling_30', 'acq_table']
    feddata_threshold = [ [cri_num_p_day_m, cri_num_p_day_f] , [cri_end_day_acc_m, cri_end_day_acc_f], [cri_stab_yes_m, cri_stab_yes_f], [cri_max_rol_avg30_m, cri_max_rol_avg30_f], [len(feddata_datatype)-1, len(feddata_datatype)-1]]

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

        # loop each day
        thres_raw = [0] * (len(feddata_datatype)* (pick_num_day_total))
        thres_binary = [0] * (len(feddata_datatype)* (pick_num_day_total))
        if mouse_thres_index != -1: # either male or female

            has_shown_first_3R_PR_QU_X = 0
            has_shown_first_RE = 0
            has_shown_first_E = 0
            pre_day_avg_pokes = 0

            # for each day
            for feddata_num_day_index in range(pick_num_day_start, pick_num_day_end+1):
                feddata_num_day_offset = feddata_num_day_index-pick_num_day_start
    
                acq_table_count = 0
                # get day filter
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
                    if feddata_num_day_offset >= 0: 
                        pre_day_count = 0
                        # default
                        if feddata_num_day_offset == 0:
                            if feddata_num_day_index > 0:
                                pre_day_from_cohort = FedDataByDay.objects.filter(mouse=mouse, fedNumDay=feddata_num_day_index-1)
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
                            if cur_day_right_pokes <= max_pre_day_pokes: 
                                thres_binary[STAB_YES*pick_num_day_total+feddata_num_day_offset] = 1
                                acq_table_count += 1
                        else:
                            max_pre_day_count = pre_day_count + pre_day_count*feddata_threshold[STAB_YES][mouse_thres_index]
                            min_pre_day_count = pre_day_count - pre_day_count*feddata_threshold[STAB_YES][mouse_thres_index]
                            thres_raw[STAB_YES*pick_num_day_total+feddata_num_day_offset] = "%d(%d-%d)" % (cur_day_count, max_pre_day_count, min_pre_day_count)
                            if cur_day_count >= min_pre_day_count and cur_day_count <= max_pre_day_count:
                                thres_binary[STAB_YES*pick_num_day_total+feddata_num_day_offset] = 1
                                acq_table_count += 1

                    # end day acc
                    cur_day_poke_acc = feddata_mouse_day[0].pokeAcc
                    thres_raw[END_DAY_ACC*pick_num_day_total+feddata_num_day_offset] = float(cur_day_poke_acc)
                    if cur_day_poke_acc > feddata_threshold[END_DAY_ACC][mouse_thres_index]:
                        thres_binary[END_DAY_ACC*pick_num_day_total+feddata_num_day_offset] = 1
                        acq_table_count += 1

                # get rolling filter
                feddata_rolling_mouse_day = feddata_cohort_rolling.filter(mouse=mouse, fedNumDay=feddata_num_day_index) 
                if feddata_rolling_mouse_day:
                    roll_max_poke_acc = feddata_rolling_mouse_day[0]['rollMaxPokeAcc']
                    thres_raw[MAX10_ROLLING_30*pick_num_day_total+feddata_num_day_offset] = float(roll_max_poke_acc)
                    if roll_max_poke_acc > feddata_threshold[MAX10_ROLLING_30][mouse_thres_index]:
                        thres_binary[MAX10_ROLLING_30*pick_num_day_total+feddata_num_day_offset] = 1
                        acq_table_count += 1

                # get final acq
                thres_raw[ACQ_TABLE*pick_num_day_total+feddata_num_day_offset] = acq_table_count
                if acq_table_count == feddata_threshold[ACQ_TABLE][mouse_thres_index]:
                    thres_binary[ACQ_TABLE*pick_num_day_total+feddata_num_day_offset] = 1

        if DEBUG:
            print(thres_raw)
            print(thres_binary)

        # thres_raw, binary ready
        mouse_data['thres_raw'] = thres_raw
        mouse_data['thres_binary'] = thres_binary

        # append mouse data
        mouse_data_list.append(mouse_data)

    # formating output
    final_acq_output = []
    for type_index in [ACQ_TABLE, NUM_P_DAY, STAB_YES, END_DAY_ACC, MAX10_ROLLING_30]:
        for mouse in mouse_data_list:
            mouse_row = {}
            mouse_row['mouse_id'] = mouse['mouse_id']
            mouse_row['mouse_name'] = mouse['mouse_name']
            mouse_row['fed'] = mouse['fed']
            mouse_row['genotype'] = mouse['genotype']
            mouse_row['sex'] = mouse['sex']
            mouse_row['data_type'] = feddata_datatype[type_index]
            # binary
            for day_index in range(pick_num_day_total):
                mouse_row[feddata_day_arr_name[day_index]] = mouse['thres_binary'][type_index*pick_num_day_total + day_index]
            # raw
            mouse_row['threshold'] = "M:%.2f F:%.2f" % (feddata_threshold[type_index][MALE], feddata_threshold[type_index][FEMALE])
            for day_index in range(pick_num_day_total):
                mouse_row[feddata_day_arr_name[day_index]+" "] = mouse['thres_raw'][type_index*pick_num_day_total + day_index]
            final_acq_output.append(mouse_row)
    # generate test_type
    for mouse in mouse_data_list:
        mouse_row = {}
        mouse_row['mouse_id'] = mouse['mouse_id']
        mouse_row['mouse_name'] = mouse['mouse_name']
        mouse_row['fed'] = mouse['fed']
        mouse_row['genotype'] = mouse['genotype']
        mouse_row['sex'] = mouse['sex']
        mouse_row['data_type'] = "test_type"
        for day_offset in range(pick_num_day_total):
            test_type = FedDataTestType.objects.filter(mouse_id=mouse['mouse_id'], fedNumDay=pick_num_day_start+day_offset)
            if test_type:
                mouse_row[feddata_day_arr_name[day_offset]] = test_type[0].testType
            else:
                mouse_row[feddata_day_arr_name[day_offset]] = ""
        final_acq_output.append(mouse_row)

    return final_acq_output

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

