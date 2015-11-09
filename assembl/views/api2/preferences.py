from simplejson import dumps, loads

from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPCreated, HTTPNotFound, HTTPBadRequest)

from assembl.auth import (
    P_READ, IF_OWNED, Everyone, CrudPermissions)
from assembl.auth.util import get_permissions
from assembl.semantic.virtuoso_mapping import get_virtuoso
from assembl.models import (
    User, Discussion, TombstonableMixin)
from assembl.models.user_key_values import *
from . import JSON_HEADER
from ..traversal import (
    PreferenceContext, PreferenceValueContext)


@view_config(context=PreferenceContext, renderer='json',
             request_method='GET', permission=P_READ)
def view_dict(request):
    preferences = request.context.preferences
    return dict(preferences)


@view_config(context=PreferenceContext, renderer='json',
             request_method='PATCH', permission=P_READ)
def patch_dict(request):
    preferences = request.context.preferences
    if not isinstance(request.json, dict):
        raise HTTPBadRequest()
    for k, v in request.json.iteritems():
        if v is None:
            del preferences[k]
        else:
            preferences[k] = v
    return dict(preferences)


@view_config(context=PreferenceValueContext, renderer='json',
             request_method='GET', permission=P_READ)
def get_value(request):
    ctx = request.context
    preferences = ctx.collection
    try:
        return preferences[ctx.key]
    except IndexError:
        raise HTTPNotFound()


@view_config(context=PreferenceValueContext, renderer='json',
             request_method='PUT', permission=P_READ, header=JSON_HEADER)
def put_value(request):
    ctx = request.context
    value = request.json
    preferences = ctx.collection
    preferences[ctx.key] = value
    return HTTPCreated()


@view_config(context=PreferenceValueContext, renderer='json',
             request_method='DELETE', permission=P_READ, header=JSON_HEADER)
def del_value(request):
    ctx = request.context
    preferences = ctx.collection
    del preferences[ctx.key]
    return {}
