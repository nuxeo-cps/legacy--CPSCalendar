##parameters=REQUEST=None

here=context.this()
here.invokeFactory('Calendars', 'Calendars')

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(here.absolute_url())
