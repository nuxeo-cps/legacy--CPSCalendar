##parameters=REQUEST=None

here=context.this()
id=REQUEST['id']
here.invokeFactory('Calendar', id)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(here.absolute_url())
