##parameters=REQUEST=None, **kw

if REQUEST is not None:
    kw.update(REQUEST.form)

from random import randrange

here = context.this()
id = str(int(DateTime()))+str(randrange(1000,10000))+('-%s' % (here.id))

all_day = kw.get('all_day')
from_date_day = kw.get('from_date_day')
if from_date_day is not None:
    # we are creating an event from a form
    from_date_day = int(from_date_day)
    from_date_month = int(kw.get('from_date_month'))
    from_date_year = int(kw.get('from_date_year'))
    from_date_hour = int(kw.get('from_date_hour'))
    from_date_minute = int(kw.get('from_date_minute'))
    ok_date = 0
    while not ok_date:
        # try to get a correct from_date_day
        try:
            from_date = DateTime(from_date_year, from_date_month, from_date_day,
                from_date_hour, from_date_minute)
        except 'DateTimeError':
            from_date_day -= 1
        else:
            ok_date = 1
    kw['from_date'] = from_date
    del kw['from_date_day']
    del kw['from_date_month']
    del kw['from_date_year']
    del kw['from_date_hour']
    del kw['from_date_minute']

    to_date_day = int(kw.get('to_date_day'))
    to_date_month = int(kw.get('to_date_month'))
    to_date_year = int(kw.get('to_date_year'))
    to_date_hour = int(kw.get('to_date_hour'))
    to_date_minute = int(kw.get('to_date_minute'))
    ok_date = 0
    while not ok_date:
        # try to get a correct to_date_day
        try:
            a_date = DateTime(to_date_year, to_date_month, to_date_day)
        except 'DateTimeError':
            to_date_day -= 1
        else:
            ok_date = 1
    if not (all_day or to_date_hour or to_date_minute):
        # end of event is midnight so automatically sets end date
        # to next day midnight
        to_date = DateTime(to_date_year, to_date_month, to_date_day) + 1
        to_date_year = to_date.year()
        to_date_month = to_date.month()
        to_date_day = to_date.day()
        
    to_date = DateTime(to_date_year, to_date_month, to_date_day,
        to_date_hour, to_date_minute)
    kw['to_date'] = to_date
    del kw['to_date_day']
    del kw['to_date_month']
    del kw['to_date_year']
    del kw['to_date_hour']
    del kw['to_date_minute']
else:
    from_date = kw['from_date']
    to_date = kw['to_date']

# if we are called by a form request, we have to be sure that
# from_date < to_date. For an all_day event, from_date and to_date
# will be switched
ok = REQUEST is None or all_day or from_date < to_date

if ok:
    ob = here.invokeFactory('Event', id, **kw)

    if REQUEST is not None:
        REQUEST.SESSION['calendar_viewed'] = from_date
        REQUEST.RESPONSE.redirect('%s/%s' % (here.absolute_url(), id))
    else:
        return ob
else:
    # the date entries are incorrect (from_date > to_date).
    # in a not all_day event, so propose to extend the event
    # to the next day
    to_date = DateTime(to_date_year, to_date_month, to_date_day) + 1
    to_date_year = to_date.year()
    to_date_month = to_date.month()
    to_date_day = to_date.day()
    to_date = DateTime(to_date_year, to_date_month, to_date_day,
        to_date_hour, to_date_minute)
    kw['to_date'] = to_date
    return context.calendar_confirmaddevent_form(**kw)
