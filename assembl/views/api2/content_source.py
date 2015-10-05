from pyramid.view import view_config
from pyramid.security import authenticated_userid
from pyramid.httpexceptions import HTTPUnauthorized, HTTPError
from dateutil.parser import parse

from assembl.auth import (P_READ, P_ADMIN_DISC, P_EXPORT, Everyone)
from assembl.models import ContentSource
from assembl.auth.util import get_permissions
from ..traversal import InstanceContext
from . import FORM_HEADER, JSON_HEADER
from assembl.tasks.source_reader import wake


@view_config(context=InstanceContext, request_method='POST',
             ctx_instance_class=ContentSource, permission=P_READ,
             header=FORM_HEADER, renderer='json', name="fetch_posts")
def fetch_posts(request):
    ctx = request.context
    csource = ctx._instance
    force_restart = request.params.get('force_restart', False)
    reimport = request.params.get('reimport', False)
    upper_bound = request.params.get('upper_limit', None)
    lower_bound = request.params.get('lower_limit', None)
    try:
        p1 = parse(upper_bound)
        p2 = parse(lower_bound)
    except:
        raise HTTPError(code=500)

    if force_restart or reimport or upper_bound or lower_bound:
        # Only discussion admins
        user_id = authenticated_userid(request) or Everyone
        permissions = get_permissions(
            user_id, ctx.get_discussion_id())
        if P_ADMIN_DISC not in permissions:
            requested = []
            if reimport:
                requested.append('reimport')
            if force_restart:
                requested.append('force restart')
            if upper_bound:
                requested.append('upper_limit')
            if lower_bound:
                requested.append('lower_limit')
            raise HTTPUnauthorized("Only discussion administrator\
                                   can "+'and'.join(requested))

    wake(csource.id, reimport, force_restart, upper_bound=upper_bound,
         lower_bound=lower_bound)  # passing the string instead of datetime
    return {"message": "Source notified",
            "name": csource.name}


@view_config(context=InstanceContext, request_method='POST',
             ctx_instance_class=ContentSource, name='export_post',
             permission=P_EXPORT, header=JSON_HEADER, renderer='json')
def export_post(request):
    # Populate the assocation table
    # MUST pass in a JSON in the form of:
    # {
    #   post_id: "", URI String of the post that was pushed out
    #   facebook_post_id: "" //String id of the post returned by Fb API
    # }
    from ...models.generic import ContentSourceIDs
    ctx = request.context
    csource = ctx._instance
    db = ContentSource.default_db
    data = request.json_body
    post_id = data.get('post_id', None)
    fb_post_id = data.get('facebook_post_id', None)
    force_restart = request.params.get('force_restart', False)
    reimport = request.params.get('reimport', False)
    upper_bound = request.params.get('upper_limit', None)
    lower_bound = request.params.get('lower_bound', None)

    if not post_id:  # or not fb_post_id:
        # post_id is necessary to establish relationship between source
        # and post. The ID of the sink, while important, might also
        # exist in the source (eg. in case of Facebook)
        return {"error": "Could not create a content \
            sink because of improper json inputs"}

    try:
        p1 = parse(upper_bound)
        p2 = parse(lower_bound)
    except:
        return {'error': 'The bound limits were not parsable'}

    else:

        try:
            cs = ContentSourceIDs(source_id=csource.id,
                                  post_id=post_id,
                                  message_id_in_source=fb_post_id)

            db.add(cs)
            db.commit()
        except:
            db.rollback()
            return {"error": "Failed on content sink transaction"}

        wake(csource.id, reimport, force_restart, upper_bound=upper_bound,
             lower_bound=lower_bound)

        return {"message": "Source notified",
                "name": csource.name}
