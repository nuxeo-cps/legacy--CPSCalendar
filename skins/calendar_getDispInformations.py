##parameters=REQUEST

# determine current calendar view
# first from REQUEST.form then from SESSION then default to week view
old_disp = REQUEST.SESSION.get('calendar_disp')
disp = REQUEST.form.get('disp')
if disp is not None:
    REQUEST.SESSION['calendar_disp'] = disp
else:
    disp = old_disp
    if disp is None:
        disp = 'week'

if disp == 'week':
    current_action = 'week_view'
elif disp == 'day':
    current_action = 'day_view'
elif disp == 'month':
    current_action = 'month_view'

# determine current selected day
selected_day = REQUEST.form.get('selected_day')
if selected_day is not None:
    selected_day = DateTime(int(selected_day))
    REQUEST.SESSION['calendar_selected'] = selected_day
else:
    selected_day = REQUEST.SESSION.get('calendar_selected')
    if selected_day is None:
        selected_day = DateTime()

# determine current viewed day
viewed_day = REQUEST.form.get('viewed_day')
if viewed_day is not None:
    viewed_day = DateTime(int(viewed_day))
    REQUEST.SESSION['calendar_viewed'] = viewed_day
else:
    viewed_day = REQUEST.SESSION.get('calendar_viewed')
    if viewed_day is None:
        viewed_day = DateTime()

time_since_daystart = viewed_day.hour()*3600+viewed_day.minute()*60+viewed_day.second()
timeTime = viewed_day.timeTime()
# XXX debug

if disp == 'day':
    start_time = DateTime(timeTime - time_since_daystart)
    end_time = start_time + 1
if disp == 'week':
    day_offset = viewed_day.dow() - 1
    if day_offset == -1: day_offset = 6
    start_time = DateTime(timeTime - time_since_daystart - day_offset*86400)
    end_time = start_time + 7
elif disp == 'month':
    day_offset = viewed_day.day() - 1
    start_time = DateTime(timeTime - time_since_daystart - day_offset*86400)
    year = start_time.year()
    month = start_time.month()
    if month < 12:
        month += 1
    else:
        month = 1
        year += 1
    end_time = DateTime(year, month, 1)

return {
    'disp': disp,
    'current_action': current_action,
    'selected_day': selected_day,
    'viewed_day': viewed_day,
    'start_time': start_time,
    'end_time': end_time,
}
