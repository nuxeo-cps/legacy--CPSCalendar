##parameters=cal_ids=[], REQUEST=None, **kw

errors = []

pr = errors.append

if REQUEST is not None:
    kw.update(REQUEST.form)

if not cal_ids:
    return context.calendar_meeting_empty()

meeting = {}
meeting['args'] = kw

try:
    from_date_string = str(kw.get('from_date','')).split('/')
    from_date_year = int(from_date_string[2])
    from_date_month = int(from_date_string[1])
    from_date_day = int(from_date_string[0])
except (ValueError, IndexError):
    pr('cpscalendar_from_incorrect_date')
ok = 0
if not errors:
    while not ok:
        try:
            from_date = DateTime(from_date_year, from_date_month, from_date_day)
            ok = 1
        except 'DateTimeError':
            from_date_day -= 1

try:
    to_date_string = str(kw.get('to_date','')).split('/')
    to_date_year = int(to_date_string[2])
    to_date_month = int(to_date_string[1])
    to_date_day = int(to_date_string[0])
except (ValueError, IndexError,):
    pr('cpscalendar_to_incorrect_date')

ok = 0
if not errors:
    while not ok:
        try:
            to_date = DateTime(to_date_year, to_date_month, to_date_day)
            ok = 1
        except 'DateTimeError':
            to_date_day -= 1

if not errors:
    days = from_date - to_date
    if abs(days) > 32:
        pr('cpscalendar_interval_month')

if errors:
    return context.calendar_meeting_error(errors=errors)

from_date_hour = int(kw['from_date_hour'])
from_date_minute = int(kw['from_date_minute'])
to_date_hour = int(kw['to_date_hour'])
to_date_minute = int(kw['to_date_minute'])

freebusy_infos = context.getFreeBusy(cal_ids, from_date, to_date,
    from_date_hour, from_date_minute, to_date_hour, to_date_minute)

meeting['freebusy_infos'] = freebusy_infos

display_ids = freebusy_infos['cal_users'].keys()

meeting['display_ids'] = display_ids

# calculate the whole freebusy
busy_infos = context.unionCals(
    *(freebusy_infos['cals_dict'].values() + [freebusy_infos['mask_cal']]),
    **{'with_free': 1}
)

meeting['busy_infos'] = busy_infos

REQUEST.SESSION['freebusy_start'] = 0

if REQUEST is not None:
    REQUEST.SESSION['meeting'] = meeting
    REQUEST.RESPONSE.redirect('%s/calendar_freebusy' % (context.absolute_url(), ))

#for key, value in meeting.items():
#    print "%s =" % (key, )
#    if same_type(value, {}):
#        for key1, value1 in value.items():
#            print '  %s = %s' % (key1, value1)
#    else:
#        print '  %s' % (value, )
#
#return printed


