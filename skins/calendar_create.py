##parameters=REQUEST=None, **kw

if REQUEST is not None:
    kw.update(REQUEST.form)

here=context.this()

id = context.compute_missing_fields('', kw)

if not id:
    id = str(int(DateTime()))

here.invokeFactory('Calendar', id, **kw)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(here.absolute_url())
