##parameters=redirect=0, REQUEST=None

mcat = context.Localizer.cpscalendar
if not int(redirect):
    if REQUEST is not None:
        REQUEST = context.REQUEST

    mtool = context.portal_membership
    if not mtool.checkPermission('View', context):
        # not authorized but we don't want to raise this error
        # since CMF will redirect it to the login form
        # and we want basic HTTP auth here
        RESPONSE = REQUEST.RESPONSE
        realm=RESPONSE.realm
        RESPONSE.setStatus(401)
        RESPONSE.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)
        RESPONSE.setBody("""<html>
<head><title>Unauthorized</title></head>
<body>
You are not authorized to access this ressource
</body>
</html>""")
        return

ical_conv = '%Y%m%dT%H%M%S'
ical_date_conv = '%Y%m%d'

def icalvalue(s):
    return unicode('\\,'.join(s.split(',')), 'latin1').encode('UTF-8')

header="""BEGIN:VCALENDAR
CALSCALE:GREGORIAN
X-WR-TIMEZONE;VALUE=TEXT:Europe/Paris
PRODID:-//Nuxeo//CPSCalendar 0.1//EN
X-WR-CALNAME;VALUE=TEXT:%s
X-WR-RELCALID;VALUE=TEXT:%s
VERSION:2.0
""" % (icalvalue(mcat(context.title_or_id())), context.absolute_url())

footer = """\
END:VCALENDAR
"""

message = header

events = context.objectValues('Event')
dtstamp = DateTime('UTC')
timezone = dtstamp.localZone()

event_header = """\
BEGIN:VEVENT
DTSTAMP:%sZ
""" % (dtstamp.strftime(ical_conv), )

event_footer = """\
END:VEVENT
"""

for event in events:
    message += event_header

    message += """\
SUMMARY:%s
UID:%s
""" % (icalvalue(mcat(event.title_or_id())), event.absolute_url())

    if event.location:
        message += """\
LOCATION:%s
""" % (icalvalue(event.location), )

    if event.all_day:
        message += """\
DTSTART;VALUE=DATE:%s
DTEND;VALUE=DATE:%s
""" % (event.from_date.strftime(ical_date_conv),
        (event.to_date+1).strftime(ical_date_conv))
    else:
        message += """\
DTSTART;TZID=%s:%s
DTEND;TZID=%s:%s
""" % (event.from_date.localZone(), event.from_date.strftime(ical_conv),
        event.to_date.localZone(), event.to_date.strftime(ical_conv))

    message += event_footer

message += footer

return message
