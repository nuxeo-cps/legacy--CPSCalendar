##parameters=viewed_day,calendar_display

if calendar_display == 'day':
    return int(viewed_day-1), int(viewed_day+1)
if calendar_display == 'week':
    return int(viewed_day-7), int(viewed_day+7)
if calendar_display == 'month':
    this_day = viewed_day
    year = this_day.year()
    month = this_day.month()
    month_start = int(DateTime(year,month,1))
    month_end = int(DateTime(year,month+1,1))
    diff = (month_end-month_start)/(24*3600)
    return int(viewed_day-diff), int(viewed_day+diff)
    
raise "Incorrect display mode %s" % calendar_display