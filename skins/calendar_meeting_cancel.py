##parameters=REQUEST=None

try:
    del REQUEST.SESSION['meeting']
except KeyError:
    pass

REQUEST.RESPONSE.redirect(context.absolute_url())
