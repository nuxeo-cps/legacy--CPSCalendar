##parameters=REQUEST=None, **kw

if REQUEST is not None:
    kw.update(REQUEST.form)

here=context.this()

id = context.compute_missing_fields('', kw)

if not id:
    id = str(int(DateTime()))

here.invokeFactory('Calendar', id, **kw)

ob = getattr(here, id)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect('%s/workgroup_localrole_form' % (ob.absolute_url(), ))
