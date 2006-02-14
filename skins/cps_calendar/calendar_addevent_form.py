##parameters=REQUEST=None

# Clean it up!
if REQUEST is not None:
    REQUEST.SESSION['meeting'] = None

return context.calendar_editevent_form(create=1)
