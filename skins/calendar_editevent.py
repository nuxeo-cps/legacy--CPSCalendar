##parameters=REQUEST=None, **kw

if REQUEST is not None:
    kw.update(REQUEST.form)

here = context.this()

from_date_day = int(kw.get('from_date_day'))
from_date_month = int(kw.get('from_date_month'))
from_date_year = int(kw.get('from_date_year'))
from_date_hour = int(kw.get('from_date_hour'))
from_date_minute = int(kw.get('from_date_minute'))
if from_date_day is not None:
    from_date = DateTime(from_date_year, from_date_month, from_date_day,
      from_date_hour, from_date_minute)
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
if to_date_day is not None:
    to_date = DateTime(to_date_year, to_date_month, to_date_day,
      to_date_hour, to_date_minute)
    kw['to_date'] = to_date
    del kw['to_date_day']
    del kw['to_date_month']
    del kw['to_date_year']
    del kw['to_date_hour']
    del kw['to_date_minute']

attendees = kw.get('attendees', [])
attendees = [att for att in attendees if att]

old_attendees = []
remove_attendees = []
for att in here.attendees:
    att_id = att['id']
    old_attendees.append(att_id)
    if att_id not in attendees:
        remove_attendees.append(att_id)

add_attendees = [att for att in attendees if att not in old_attendees]

new_attendees = [att for att in here.attendees if att['id'] not in remove_attendees]

for attendee in add_attendees:
    new_attendees.append({'id': attendee, 'status': 'unconfirmed'})

kw['attendees'] = new_attendees
here.edit(**kw)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(here.absolute_url())

