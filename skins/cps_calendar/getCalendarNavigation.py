##parameters=finder, root_uid, current_uid=None, REQUEST=None
# $Id$
from Products.CPSNavigation.ConfNavigation import ConfNavigation
from Products.CPSNavigation.ZODBNavigation import ZODBNavigation
from Products.CPSNavigation.CPSNavigation import CPSNavigation
from Products.CPSNavigation.LDAPDirectoryNavigation import \
     LDAPDirectoryNavigation
from Products.CPSNavigation.CPSDirectoryNavigation import \
     CPSDirectoryNavigation

if REQUEST and REQUEST.has_key('current_uid'):
    current_uid = REQUEST.get('current_uid')
if not current_uid:
    current_uid = root_uid

next_uid = current_uid
while 1:
    current_uid = next_uid
    docurl = context.portal_url.getPortalPath() + '/' + current_uid
    doc = context.restrictedTraverse(docurl, None)
    next_uid = '/'.join(next_uid.split('/')[:-1])
    if not (doc and doc.meta_type in ('CPS Proxy Folder',
                                      'CPS Proxy Folderish Document')):
        break

# current_uid = context.portal_url.getRelativeContentURL(context)
nav = CPSNavigation(root_uid=root_uid,
                    current_uid=current_uid,
                    context=context,
                    include_root=0,
                    no_leaves=0,
                    # filter_tree_ptypes=('Workspace',),
                    # filter_listing_ptypes=('Link',),
                    sort_listing_by='title',
                    sort_listing_direction='asc',
                    batch_size=15,
                    request_form=REQUEST.form,
                    )
# XXX try to get another tree and concatenate ?

tree = None
if not REQUEST.get('search'):
    tree = nav.getTree()
listing, listing_info, batch_info = nav.getListing()
return tree, listing, batch_info, listing_info, finder
