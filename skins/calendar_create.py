##parameters=REQUEST=None, **kw

if REQUEST is not None:
    kw.update(REQUEST.form)

here=context.this()

if kw.has_key('id'):
    id = kw['id']
elif kw.has_key('default_id_from'):
    id = kw[kw['default_id_from']]
else:
    id = str(int(DateTime()))
    
id = context.checkid(compute_from=id)

here.invokeFactory('Calendar', id, **kw)

ob = getattr(here, id)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect('%s/folder_localrole_form' % (ob.absolute_url(), ))
