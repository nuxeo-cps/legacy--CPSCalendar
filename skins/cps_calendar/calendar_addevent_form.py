##parameters=REQUEST

# Clean it up!
REQUEST.SESSION['meeting'] = None

return context.calendar_editevent_form(create=1)
