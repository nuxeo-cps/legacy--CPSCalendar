##parameters=REQUEST

kw = REQUEST.form

kw['to_date'] = DateTime(kw['to_date'])
kw['from_date'] = DateTime(kw['from_date'])

context.calendar_addevent(REQUEST=REQUEST, **kw)
