##parameters=title, location, from_date, from_date_hour, from_date_minute, duration, event_status, category, cal_ids=[], REQUEST=None

here = context.this()

attendees = [here.getAttendeeInfo(id, 1) for id in cal_ids]

from_date = DateTime(from_date)
from_date_day = from_date.day()
from_date_month = from_date.month()
from_date_year = from_date.year()
from_date = DateTime(from_date_year, from_date_month, from_date_day,
    from_date_hour, from_date_minute)

to_date = int(from_date) + duration*60
to_date = DateTime(to_date)

from random import randrange

id = str(int(DateTime()))+str(randrange(1000,10000))+('-%s' % (here.id))

here.invokeFactory('Event', id, title=title, location=location,
    from_date=from_date, to_date=to_date, all_day=0,
    event_status=event_status, category=category, attendees=attendees,
    transparent=0)

try:
    del REQUEST.SESSION['meeting']
    del REQUEST.SESSION['freebusy_start']
except KeyError:
    pass

REQUEST.RESPONSE.redirect('%s/%s' % (here.absolute_url(), id))
