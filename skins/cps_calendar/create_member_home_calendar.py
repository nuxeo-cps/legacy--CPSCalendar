##parameters=REQUEST=None
# $ Id: $
# Just create an calendar in the user's home folder with «calendar» id

portal = context.portal_url.getPortalObject()

portal.portal_cpscalendar.createMemberCalendar()

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(
        '%s/calendar' % portal.portal_cpscalendar.getHomeCalendarUrl())

return