##parameters=REQUEST=None

here=context.this()
here.invokeFactory('Calendars', 'Calendars')

if REQUEST:
    REQUEST.RESPONSE.redirect(here.absolute_url())
