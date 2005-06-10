##parameters=REQUEST
# $Id$

from zLOG import LOG, DEBUG

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

# determine current viewed day
viewed_day = REQUEST.form.get('viewed_day')
if viewed_day is not None:
    viewed_day = DateTime(int(viewed_day))
    REQUEST.SESSION['calendar_viewed'] = viewed_day
else:
    viewed_day = REQUEST.SESSION.get('calendar_viewed')
    if viewed_day is None:
        viewed_day = DateTime()

# determine current selected day
from_date = REQUEST.form.get('from_date')
selected_day = REQUEST.form.get('selected_day')
if from_date is not None:
    locale = context.translation_service.getSelectedLanguage()
    selected_day = context.portal_cpscalendar.stringToDateTime(from_date,locale)
    LOG('CPSCAL', DEBUG, "selected_day from from_date = %s" % selected_day)
elif selected_day is not None:
    selected_day = DateTime(int(selected_day))
    LOG('CPSCAL', DEBUG, "selected_day from selected_day = %s" % selected_day)
else:
    selected_day = viewed_day
    LOG('CPSCAL', DEBUG, "selected_day defaulting to viewed_day = %s" % selected_day)

year = viewed_day.year()
month = viewed_day.month()
day = viewed_day.day()

if disp == 'day':
    start_time = DateTime(year, month, day)
    end_time = start_time + 1
if disp == 'week':
    day_offset = viewed_day.dow() - 1
    if day_offset == -1: day_offset = 6
    start_time = DateTime(year, month, day) - day_offset
    end_time = start_time + 7
elif disp == 'month':
    start_time = DateTime(year, month, 1)
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
