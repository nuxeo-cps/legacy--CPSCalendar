##parameters=start, REQUEST=None

start = int(start)
if start < 0:
    start = 0

REQUEST.SESSION['freebusy_start'] = start

REQUEST.RESPONSE.redirect('%s/calendar_freebusy' % (context.absolute_url(), ))
