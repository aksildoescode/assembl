import os.path
import graphene
from graphene.relay import Node
from graphene_sqlalchemy import SQLAlchemyObjectType
from urlparse import urljoin

from assembl import models
from assembl.auth import CrudPermissions

import assembl.graphql.docstrings as docs
from .attachment import Attachment
from .document import Document
from .types import SecureObjectType
from .langstring import (
    LangStringEntry, LangStringEntryInput, resolve_langstring,
    resolve_langstring_entries, update_langstring_from_input_entries)
from .utils import (
    abort_transaction_on_exception,
    create_attachment,
    update_attachment,
    get_attachments_with_purpose,
    get_attachment_with_purpose,
    DateTime)
from .idea import TagResult, SentimentAnalysisResult
from .permissions_helpers import require_cls_permission, require_instance_permission
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('assembl')


class URLMeta(graphene.ObjectType):
    local = graphene.Boolean()
    url = graphene.String(required=True)


# Mostly fields related to the discussion title and landing page
class Discussion(SecureObjectType, SQLAlchemyObjectType):
    __doc__ = docs.Discussion.__doc__

    class Meta:
        model = models.Discussion
        interfaces = (Node, )
        only_fields = ('id',)

    homepage_url = graphene.String(description=docs.Discussion.homepage_url)
    title = graphene.String(
        lang=graphene.String(description=docs.Default.required_language_input),
        description=docs.Discussion.title)
    title_entries = graphene.List(LangStringEntry, description=docs.Default.langstring_entries)
    subtitle = graphene.String(
        lang=graphene.String(description=docs.Default.required_language_input),
        description=docs.Discussion.subtitle)
    subtitle_entries = graphene.List(LangStringEntry, description=docs.Default.langstring_entries)
    button_label = graphene.String(
        lang=graphene.String(description=docs.Default.required_language_input),
        description=docs.Discussion.button_label)
    button_label_entries = graphene.List(LangStringEntry, description=docs.Default.langstring_entries)
    header_image = graphene.Field(Document, description=docs.Discussion.header_image)
    logo_image = graphene.Field(Document, description=docs.Discussion.logo_image)
    start_date = graphene.Field(DateTime, description=docs.Discussion.start_date)
    end_date = graphene.Field(DateTime, description=docs.Discussion.end_date)
    top_keywords = graphene.List(TagResult, description=docs.Discussion.top_keywords)
    nlp_sentiment = graphene.Field(SentimentAnalysisResult, description=docs.Discussion.nlp_sentiment)
    slug = graphene.String(description=docs.Discussion.slug)
    login_data = graphene.Field(URLMeta, next_view=graphene.String(required=False))

    def resolve_homepage_url(self, args, context, info):
        # TODO: Remove this resolver and add URLString to
        # the Graphene SQLA converters list
        return self.homepage_url

    def resolve_title(self, args, context, info):
        """Title value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.title, args.get('lang'))

    def resolve_title_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.title:
            return resolve_langstring_entries(discussion, 'title')

        return []

    def resolve_subtitle(self, args, context, info):
        """Subtitle value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.subtitle, args.get('lang'))

    def resolve_subtitle_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.subtitle:
            return resolve_langstring_entries(discussion, 'subtitle')

        return []

    def resolve_button_label(self, args, context, info):
        """Button label value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.button_label, args.get('lang'))

    def resolve_button_label_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.button_label:
            return resolve_langstring_entries(discussion, 'button_label')

        return []

    def resolve_header_image(self, args, context, info):
        LANDING_PAGE_HEADER_IMAGE = models.AttachmentPurpose.LANDING_PAGE_HEADER_IMAGE.value
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        for attachment in discussion.attachments:
            if attachment.attachmentPurpose == LANDING_PAGE_HEADER_IMAGE:
                return attachment.document

    def resolve_logo_image(self, args, context, info):
        LANDING_PAGE_LOGO_IMAGE = models.AttachmentPurpose.LANDING_PAGE_LOGO_IMAGE.value
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        for attachment in discussion.attachments:
            if attachment.attachmentPurpose == LANDING_PAGE_LOGO_IMAGE:
                return attachment.document

    def resolve_login_data(self, args, context, info):
        # if the debate is public, but has an SSO set and a prefernece to redirect publically
        # this URL would be used
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        prefs = discussion.preferences
        next_view = args.get('next_view') or False
        auth_backend = prefs.get('authorization_server_backend') or None
        landing_page = prefs.get('landing_page') or False
        if auth_backend and landing_page:
            from assembl.views.auth.views import get_social_autologin
            route = get_social_autologin(context, discussion, next_view)
            local = False
            url = urljoin(discussion.get_base_url(), route)
        else:
            # Just a regular discussion login, but a route from perspective of React-Router
            # Do not pass any next view by default. It's responsibility of the caller
            from assembl.lib.frontend_urls import FrontendUrls
            furl = FrontendUrls(discussion)
            route = furl.get_frontend_url('ctxLogin')
            if next_view:
                route = furl.append_query_string(route, next=next_view)
            local = True
            url = route
        return URLMeta(local=local, url=url)

    def resolve_top_keywords(self, args, context, info):
        result = self.top_keywords()
        return [TagResult(score=r.score, value=r.value, count=r.count) for r in result]

    def resolve_nlp_sentiment(self, args, context, info):
        result = self.sentiments()
        return SentimentAnalysisResult(**result._asdict())

    def resolve_start_date(self, args, context, info):
        from sqlalchemy import func
        if self.active_start_date:
            return self.active_start_date
        discussion_id = context.matchdict['discussion_id']
        db = models.Discussion.default_db
        result = db.query(func.min(models.TimelineEvent.start)).filter(models.TimelineEvent.discussion_id == discussion_id).first()
        if result:
            result = result[0]
            return result

    def resolve_end_date(self, args, context, info):
        from sqlalchemy import func
        if self.active_end_date:
            return self.active_end_date
        discussion_id = context.matchdict['discussion_id']
        db = models.Discussion.default_db
        result = db.query(func.max(models.TimelineEvent.end)).filter(models.TimelineEvent.discussion_id == discussion_id).first()
        if result:
            result = result[0]
            return result


class UpdateDiscussion(graphene.Mutation):
    __doc__ = docs.UpdateDiscussion.__doc__

    class Input:
        title_entries = graphene.List(LangStringEntryInput, description=docs.UpdateDiscussion.title_entries)
        subtitle_entries = graphene.List(LangStringEntryInput, description=docs.UpdateDiscussion.subtitle_entries)
        button_label_entries = graphene.List(LangStringEntryInput, description=docs.UpdateDiscussion.button_label_entries)
        header_image = graphene.String(description=docs.UpdateDiscussion.header_image)
        logo_image = graphene.String(description=docs.UpdateDiscussion.logo_image)
        start_date = DateTime(description=docs.UpdateDiscussion.start_date)
        end_date = DateTime(description=docs.UpdateDiscussion.end_date)

    discussion = graphene.Field(lambda: Discussion)

    @staticmethod
    @abort_transaction_on_exception
    def mutate(root, args, context, info):
        cls = models.Discussion
        discussion_id = context.matchdict['discussion_id']
        discussion = cls.get(discussion_id)

        require_instance_permission(CrudPermissions.UPDATE, discussion, context)

        with cls.default_db.no_autoflush as db:
            title_entries = args.get('title_entries')
            if title_entries is not None and len(title_entries) == 0:
                raise Exception(
                    'Title entries needs at least one entry')
                # Better to have this message than
                # 'NoneType' object has no attribute 'owner_object'
                # when creating the saobj below if title=None

            update_langstring_from_input_entries(
                discussion, 'title', title_entries)

            subtitle_entries = args.get('subtitle_entries')
            update_langstring_from_input_entries(
                discussion, 'subtitle', subtitle_entries)

            button_label_entries = args.get('button_label_entries')
            update_langstring_from_input_entries(
                discussion, 'button_label', button_label_entries)

            # add uploaded header image as an attachment to the discussion
            LANDING_PAGE_HEADER_IMAGE = models.AttachmentPurpose.LANDING_PAGE_HEADER_IMAGE.value
            image = args.get('header_image')
            if image is not None:
                update_attachment(
                    discussion,
                    models.DiscussionAttachment,
                    image,
                    discussion.attachments,
                    LANDING_PAGE_HEADER_IMAGE,
                    db,
                    context
                )

            # add uploaded logo image as an attachment to the discussion
            LANDING_PAGE_LOGO_IMAGE = models.AttachmentPurpose.LANDING_PAGE_LOGO_IMAGE.value
            image = args.get('logo_image')
            if image is not None:
                update_attachment(
                    discussion,
                    models.DiscussionAttachment,
                    image,
                    discussion.attachments,
                    LANDING_PAGE_LOGO_IMAGE,
                    db,
                    context
                )

        start_date = args.get('start_date', None)
        end_date = args.get('end_date', None)
        if start_date:
            discussion.active_start_date = start_date.replace(tzinfo=None)
        if end_date:
            discussion.active_end_date = end_date.replace(tzinfo=None)

        db.flush()
        discussion = cls.get(discussion_id)
        return UpdateDiscussion(discussion=discussion)


class LocalePreference(graphene.ObjectType):
    __doc__ = docs.LocalePreference.__doc__

    locale = graphene.String(description=docs.LocalePreference.locale)
    name = graphene.String(in_locale=graphene.String(required=True), description=docs.LocalePreference.name)
    native_name = graphene.String(description=docs.LocalePreference.native_name)

    def resolve_name(self, args, context, info):
        in_locale = args.get('in_locale') or None
        locale_model = models.Locale.get_or_create(in_locale)

        name = models.LocaleLabel.names_of_locales_in_locale([self.locale],
                                                             locale_model)
        if not name:
            # If the locale label does not exist, fallback on English
            locale_model = models.Locale.get_or_create('en')
            name = models.LocaleLabel.names_of_locales_in_locale([self.locale],
                                                                 locale_model)

        return name[self.locale]

    def resolve_native_name(self, args, context, info):
        locale = self.locale
        if locale == 'zh_Hans':  # we have the native name only for zh
            locale = 'zh'

        locale_model = models.Locale.get_or_create(locale)
        name = models.LocaleLabel.names_of_locales_in_locale([locale],
                                                             locale_model)
        if not name:
            # If the locale label does not exist, fallback on English
            locale_model = models.Locale.get_or_create('en')
            name = models.LocaleLabel.names_of_locales_in_locale([locale],
                                                                 locale_model)

        return name[locale]


class DiscussionPreferences(graphene.ObjectType):
    __doc__ = docs.DiscussionPreferences.__doc__
    languages = graphene.List(LocalePreference, description=docs.DiscussionPreferences.languages)
    tab_title = graphene.String(description=docs.DiscussionPreferences.tab_title)
    favicon = graphene.Field(Document, description=docs.DiscussionPreferences.favicon)
    logo = graphene.Field(Document, description=docs.DiscussionPreferences.logo)
    with_moderation = graphene.Boolean(description=docs.DiscussionPreferences.with_moderation)
    slug = graphene.String(required=True, description=docs.DiscussionPreferences.slug)
    old_slugs = graphene.List(graphene.String, required=True, description=docs.DiscussionPreferences.old_slugs)

    def resolve_tab_title(self, args, context, info):
        return self.get('tab_title', 'Assembl')

    def resolve_languages(self, args, context, info):
        locales = self.get('preferred_locales', [])
        return [LocalePreference(locale=x) for x in locales]

    def resolve_favicon(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        attachment = get_attachment_with_purpose(
            discussion.attachments, models.AttachmentPurpose.FAVICON.value)
        return attachment and attachment.document

    def resolve_logo(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        attachment = get_attachment_with_purpose(
            discussion.attachments, models.AttachmentPurpose.LOGO.value)
        return attachment and attachment.document

    def resolve_with_moderation(self, args, context, info):
        return self.get('with_moderation')

    def resolve_slug(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return discussion.slug

    def resolve_old_slugs(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return [old_slug.slug for old_slug in discussion.old_slugs]


class ResourcesCenter(graphene.ObjectType):
    __doc__ = docs.ResourcesCenter.__doc__
    title = graphene.String(lang=graphene.String(), description=docs.ResourcesCenter.title)
    title_entries = graphene.List(LangStringEntry, description=docs.ResourcesCenter.title_entries)
    header_image = graphene.Field(Document, description=docs.ResourcesCenter.header_image)

    def resolve_title(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(
            discussion.resources_center_title, args.get('lang'))

    def resolve_title_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring_entries(discussion, 'resources_center_title')

    def resolve_header_image(self, args, context, info):
        RESOURCES_CENTER_HEADER_IMAGE = models.AttachmentPurpose.RESOURCES_CENTER_HEADER_IMAGE.value
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        for attachment in discussion.attachments:
            if attachment.attachmentPurpose == RESOURCES_CENTER_HEADER_IMAGE:
                return attachment.document


class LegalContents(graphene.ObjectType):
    __doc__ = docs.LegalContents.__doc__
    legal_notice = graphene.String(lang=graphene.String(), description=docs.LegalContents.legal_notice)
    terms_and_conditions = graphene.String(lang=graphene.String(), description=docs.LegalContents.terms_and_conditions)
    legal_notice_entries = graphene.List(LangStringEntry, description=docs.LegalContents.legal_notice_entries)
    terms_and_conditions_entries = graphene.List(LangStringEntry, description=docs.LegalContents.terms_and_conditions_entries)
    cookies_policy = graphene.String(lang=graphene.String(), description=docs.LegalContents.cookies_policy)
    privacy_policy = graphene.String(lang=graphene.String(), description=docs.LegalContents.privacy_policy)
    cookies_policy_entries = graphene.List(LangStringEntry, description=docs.LegalContents.cookies_policy_entries)
    privacy_policy_entries = graphene.List(LangStringEntry, description=docs.LegalContents.privacy_policy_entries)
    user_guidelines = graphene.String(lang=graphene.String(), description=docs.LegalContents.user_guidelines)
    user_guidelines_entries = graphene.List(LangStringEntry, description=docs.LegalContents.user_guidelines_entries)
    legal_notice_attachments = graphene.List(Attachment, description=docs.LegalContents.legal_notice_attachments)
    terms_and_conditions_attachments = graphene.List(Attachment, description=docs.LegalContents.terms_and_conditions_attachments)
    cookies_policy_attachments = graphene.List(Attachment, description=docs.LegalContents.cookies_policy_attachments)
    privacy_policy_attachments = graphene.List(Attachment, description=docs.LegalContents.privacy_policy_attachments)
    user_guidelines_attachments = graphene.List(Attachment, description=docs.LegalContents.user_guidelines_attachments)
    mandatory_legal_contents_validation = graphene.Boolean(required=True, description=docs.LegalContents.mandatory_legal_contents_validation)

    def resolve_legal_notice(self, args, context, info):
        """Legal notice value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.legal_notice, args.get('lang'))

    def resolve_terms_and_conditions(self, args, context, info):
        """Terms and conditions value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.terms_and_conditions, args.get('lang'))

    def resolve_legal_notice_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.legal_notice:
            return resolve_langstring_entries(discussion, 'legal_notice')

        return []

    def resolve_terms_and_conditions_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.terms_and_conditions:
            return resolve_langstring_entries(discussion, 'terms_and_conditions')

        return []

    def resolve_cookies_policy(self, args, context, info):
        """Cookies policy value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.cookies_policy, args.get('lang'))

    def resolve_privacy_policy(self, args, context, info):
        """Privacy policy value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.privacy_policy, args.get('lang'))

    def resolve_cookies_policy_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.cookies_policy:
            return resolve_langstring_entries(discussion, 'cookies_policy')

        return []

    def resolve_privacy_policy_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.privacy_policy:
            return resolve_langstring_entries(discussion, 'privacy_policy')

        return []

    def resolve_user_guidelines(self, args, context, info):
        """User guidelines value in given locale."""
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return resolve_langstring(discussion.user_guidelines, args.get('lang'))

    def resolve_user_guidelines_entries(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        if discussion.user_guidelines:
            return resolve_langstring_entries(discussion, 'user_guidelines')

        return []

    def resolve_legal_notice_attachments(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return get_attachments_with_purpose(discussion.attachments, models.AttachmentPurpose.LEGAL_NOTICE_ATTACHMENT.value)

    def resolve_terms_and_conditions_attachments(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return get_attachments_with_purpose(discussion.attachments, models.AttachmentPurpose.TERMS_AND_CONDITIONS_ATTACHMENT.value)

    def resolve_cookies_policy_attachments(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return get_attachments_with_purpose(discussion.attachments, models.AttachmentPurpose.COOKIES_POLICY_ATTACHMENT.value)

    def resolve_privacy_policy_attachments(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return get_attachments_with_purpose(discussion.attachments, models.AttachmentPurpose.PRIVACY_POLICY_ATTACHMENT.value)

    def resolve_user_guidelines_attachments(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return get_attachments_with_purpose(discussion.attachments, models.AttachmentPurpose.USER_GUIDELINES_ATTACHMENT.value)

    def resolve_mandatory_legal_contents_validation(self, args, context, info):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        return discussion.preferences['mandatory_legal_contents_validation']


class UpdateResourcesCenter(graphene.Mutation):
    __doc__ = docs.UpdateResourcesCenter.__doc__

    class Input:
        title_entries = graphene.List(LangStringEntryInput, description=docs.UpdateResourcesCenter.title_entries)
        header_image = graphene.String(description=docs.UpdateResourcesCenter.header_image)

    resources_center = graphene.Field(lambda: ResourcesCenter)

    @staticmethod
    @abort_transaction_on_exception
    def mutate(root, args, context, info):
        RESOURCES_CENTER_HEADER_IMAGE = models.AttachmentPurpose.RESOURCES_CENTER_HEADER_IMAGE.value
        cls = models.Discussion
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)

        require_instance_permission(CrudPermissions.UPDATE, discussion, context)

        with cls.default_db.no_autoflush:
            db = discussion.db
            title_entries = args.get('title_entries')
            if title_entries is not None and len(title_entries) == 0:
                raise Exception(
                    'Resources center title entries needs at least one entry')
                # Better to have this message than
                # 'NoneType' object has no attribute 'owner_object'
                # when creating the saobj below if title=None

            update_langstring_from_input_entries(
                discussion, 'resources_center_title', title_entries)

            # add uploaded image as an attachment to the discussion
            image = args.get('header_image')
            if image is not None:
                filename = os.path.basename(context.POST[image].filename)
                mime_type = context.POST[image].type
                document = models.File(
                    discussion=discussion,
                    mime_type=mime_type,
                    title=filename)
                document.add_file_data(context.POST[image].file)

                # if there is already an IMAGE, remove it with the
                # associated document
                header_images = [
                    att for att in discussion.attachments
                    if att.attachmentPurpose == RESOURCES_CENTER_HEADER_IMAGE
                ]
                if header_images:
                    header_image = header_images[0]
                    header_image.document.delete_file()
                    db.delete(header_image.document)
                    discussion.attachments.remove(header_image)

                db.add(models.DiscussionAttachment(
                    document=document,
                    discussion=discussion,
                    creator_id=context.authenticated_userid,
                    title=filename,
                    attachmentPurpose=RESOURCES_CENTER_HEADER_IMAGE
                ))

        db.flush()
        resources_center = ResourcesCenter()
        return UpdateResourcesCenter(resources_center=resources_center)


class UpdateDiscussionPreferences(graphene.Mutation):
    __doc__ = docs.UpdateDiscussionPreferences.__doc__

    class Input:
        languages = graphene.List(graphene.String, description=docs.UpdateDiscussionPreferences.languages)
        tab_title = graphene.String(description=docs.UpdateDiscussionPreferences.tab_title)
        # this is the identifier of the part in a multipart POST
        favicon = graphene.String(description=docs.UpdateDiscussionPreferences.favicon)
        logo = graphene.String(description=docs.UpdateDiscussionPreferences.logo)
        with_moderation = graphene.Boolean(description=docs.UpdateDiscussionPreferences.with_moderation)
        slug = graphene.String(description=docs.UpdateDiscussionPreferences.slug)

    preferences = graphene.Field(lambda: DiscussionPreferences)

    @staticmethod
    @abort_transaction_on_exception
    def mutate(root, args, context, info):
        cls = models.Preferences
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        require_cls_permission(CrudPermissions.UPDATE, cls, context)
        languages = args.get('languages', None)
        tab_title = args.get('tab_title', None)
        favicon = args.get('favicon', None)
        logo = args.get('logo', None)
        with_moderation = args.get('with_moderation', None)
        slug = args.get('slug', None)
        with cls.default_db.no_autoflush as db:
            if languages is not None:
                if not languages:
                    error = _("Must pass at least one language to be saved")
                    raise Exception(context.localizer.translate(error))

                discussion.discussion_locales = languages

            if tab_title:
                discussion.preferences['tab_title'] = tab_title

            if favicon:
                update_attachment(
                    discussion,
                    models.DiscussionAttachment,
                    favicon,
                    discussion.attachments,
                    models.AttachmentPurpose.FAVICON.value,
                    db,
                    context
                )

            if logo:
                update_attachment(
                    discussion,
                    models.DiscussionAttachment,
                    logo,
                    discussion.attachments,
                    models.AttachmentPurpose.LOGO.value,
                    db,
                    context
                )

            if with_moderation is not None:
                discussion.preferences['with_moderation'] = with_moderation

            if slug is not None:
                if slug != discussion.slug:
                    if models.OldSlug.query.filter(
                            models.OldSlug.slug == slug
                            ).filter(models.OldSlug.discussion_id != discussion.id).first() is not None:
                        error = _("This slug is an old slug of another debate, you can't use it.")
                        raise Exception(context.localizer.translate(error))

                    if models.Discussion.query.filter(
                            models.Discussion.slug == slug
                            ).first() is not None:
                        error = _("This slug is already used by another debate, you can't use it.")
                        raise Exception(context.localizer.translate(error))

                    if discussion.slug not in [old_slug.slug for old_slug in discussion.old_slugs]:
                        db.add(models.OldSlug(
                            discussion=discussion,
                            slug=discussion.slug))

                    discussion.slug = slug

            db.flush()

        return UpdateDiscussionPreferences(preferences=discussion.preferences)


def update_legal_contents_attachments(context, discussion, new_attachments, purpose):
    """Create, update, delete legal contents attachments for a legal contents field."""
    original_ln_attachments = get_attachments_with_purpose(
        discussion.attachments, purpose)
    original_attachments_doc_ids = []
    if original_ln_attachments:
        original_attachments_doc_ids = [
            str(a.document_id) for a in original_ln_attachments]

    for document_id in new_attachments:
        if document_id not in original_attachments_doc_ids:
            create_attachment(
                discussion,
                models.DiscussionAttachment,
                purpose,
                context,
                document_id=document_id
            )

    # delete attachments that has been removed
    documents_to_delete = set(original_attachments_doc_ids) - set(new_attachments)
    for document_id in documents_to_delete:
        with models.Discussion.default_db.no_autoflush:
            document = models.Document.get(document_id)
            attachments = discussion.db.query(
                models.DiscussionAttachment
            ).filter_by(
                attachmentPurpose=purpose,
                discussion_id=discussion.id,
                document_id=document_id
            ).all()
            document.delete_file()
            discussion.db.delete(document)
            for attachment in attachments:
                discussion.attachments.remove(attachment)


class UpdateLegalContents(graphene.Mutation):
    __doc__ = docs.UpdateLegalContents.__doc__

    class Input:
        legal_notice_attachments = graphene.List(graphene.String, description=docs.UpdateLegalContents.legal_notice_attachments)
        terms_and_conditions_attachments = graphene.List(graphene.String, description=docs.UpdateLegalContents.terms_and_conditions_attachments)
        cookies_policy_attachments = graphene.List(graphene.String, description=docs.UpdateLegalContents.cookies_policy_attachments)
        privacy_policy_attachments = graphene.List(graphene.String, description=docs.UpdateLegalContents.privacy_policy_attachments)
        user_guidelines_attachments = graphene.List(graphene.String, description=docs.UpdateLegalContents.user_guidelines_attachments)
        legal_notice_entries = graphene.List(LangStringEntryInput, description=docs.UpdateLegalContents.legal_notice_entries)
        terms_and_conditions_entries = graphene.List(LangStringEntryInput, description=docs.UpdateLegalContents.terms_and_conditions_entries)
        cookies_policy_entries = graphene.List(LangStringEntryInput, description=docs.UpdateLegalContents.cookies_policy_entries)
        privacy_policy_entries = graphene.List(LangStringEntryInput, description=docs.UpdateLegalContents.privacy_policy_entries)
        user_guidelines_entries = graphene.List(LangStringEntryInput, description=docs.UpdateLegalContents.user_guidelines_entries)
        mandatory_legal_contents_validation = graphene.Boolean(required=True, description=docs.UpdateLegalContents.mandatory_legal_contents_validation)

    legal_contents = graphene.Field(lambda: LegalContents)

    @staticmethod
    @abort_transaction_on_exception
    def mutate(root, args, context, info):
        LEGAL_NOTICE_ATTACHMENT = models.AttachmentPurpose.LEGAL_NOTICE_ATTACHMENT.value
        TERMS_AND_CONDITIONS_ATTACHMENT = models.AttachmentPurpose.TERMS_AND_CONDITIONS_ATTACHMENT.value
        COOKIES_POLICY_ATTACHMENT = models.AttachmentPurpose.COOKIES_POLICY_ATTACHMENT.value
        PRIVACY_POLICY_ATTACHMENT = models.AttachmentPurpose.PRIVACY_POLICY_ATTACHMENT.value
        USER_GUIDELINES_ATTACHMENT = models.AttachmentPurpose.USER_GUIDELINES_ATTACHMENT.value
        cls = models.Discussion
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        mandatory_legal_contents_validation = args.get('mandatory_legal_contents_validation')

        require_instance_permission(CrudPermissions.UPDATE, discussion, context)

        with cls.default_db.no_autoflush as db:
            legal_notice_entries = args.get('legal_notice_entries')
            if legal_notice_entries is not None and len(legal_notice_entries) == 0:
                raise Exception(
                    'Legal notice entries needs at least one entry')
                # Better to have this message than
                # 'NoneType' object has no attribute 'owner_object'
                # when creating the saobj below if title=None

            update_langstring_from_input_entries(
                discussion, 'legal_notice', legal_notice_entries)

            terms_and_conditions_entries = args.get(
                'terms_and_conditions_entries')
            if terms_and_conditions_entries is not None and len(terms_and_conditions_entries) == 0:
                raise Exception(
                    'Terms and conditions entries needs at least one entry')
                # Better to have this message than
                # 'NoneType' object has no attribute 'owner_object'
                # when creating the saobj below if title=None

            update_langstring_from_input_entries(
                discussion, 'terms_and_conditions', terms_and_conditions_entries)

            cookies_policy_entries = args.get('cookies_policy_entries')
            if cookies_policy_entries is not None and len(cookies_policy_entries) == 0:
                raise Exception(
                    'Cookies policy entries needs at least one entry')

            update_langstring_from_input_entries(
                discussion, 'cookies_policy', cookies_policy_entries)

            privacy_policy_entries = args.get('privacy_policy_entries')
            if privacy_policy_entries is not None and len(privacy_policy_entries) == 0:
                raise Exception(
                    'Privacy policy entries need to be at least one entry'
                )

            update_langstring_from_input_entries(
                discussion, 'privacy_policy', privacy_policy_entries)

            user_guidelines_entries = args.get('user_guidelines_entries')
            if user_guidelines_entries is not None and len(user_guidelines_entries) == 0:
                raise Exception(
                    'User guidelines entries need to be at least one entry'
                )

            update_langstring_from_input_entries(
                discussion, 'user_guidelines', user_guidelines_entries
            )

            legal_contents_attachments_by_purpose = [
                (args.get('legal_notice_attachments', []), LEGAL_NOTICE_ATTACHMENT),
                (args.get('terms_and_conditions_attachments', []), TERMS_AND_CONDITIONS_ATTACHMENT),
                (args.get('cookies_policy_attachments', []), COOKIES_POLICY_ATTACHMENT),
                (args.get('privacy_policy_attachments', []), PRIVACY_POLICY_ATTACHMENT),
                (args.get('user_guidelines_attachments', []), USER_GUIDELINES_ATTACHMENT),
            ]
            for new_attachments, purpose in legal_contents_attachments_by_purpose:
                update_legal_contents_attachments(
                    context,
                    discussion,
                    new_attachments,
                    purpose
                )

            discussion.preferences['mandatory_legal_contents_validation'] = mandatory_legal_contents_validation

        db.flush()
        legal_contents = LegalContents()
        return UpdateLegalContents(legal_contents=legal_contents)


class VisitsAnalytics(graphene.ObjectType):
    __doc__ = docs.VisitsAnalytics.__doc__
    sum_visits_length = graphene.Int(description=docs.VisitsAnalytics.sum_visits_length)
    nb_pageviews = graphene.Int(description=docs.VisitsAnalytics.nb_pageviews)
    nb_uniq_pageviews = graphene.Int(description=docs.VisitsAnalytics.nb_uniq_pageviews)

    @classmethod
    def query_analytics(cls, args, context, info, single_metric=None):
        discussion_id = context.matchdict['discussion_id']
        discussion = models.Discussion.get(discussion_id)
        start = args.get('start_date') or None
        end = args.get('end_date') or None
        try:
            if single_metric is not None:
                data = discussion.get_visits_time_series_analytics(start, end, [single_metric])
                return data[single_metric]
            else:
                return discussion.get_visits_time_series_analytics(start, end)
        except ValueError:
            return None
        except Exception:
            context.logger().exception('Error with Matomo request')
            return None

    def generic_resolver(self, args, context, info, field_name):
        val = getattr(self, field_name, None)
        if val is not None:
            return val
        return VisitsAnalytics.query_analytics(args, context, info, field_name)

    @classmethod
    def build_from_full_query(cls, args, context, info):
        data = VisitsAnalytics.query_analytics(args, context, info)
        if not data:
            return VisitsAnalytics(sum_visits_length=None, nb_pageviews=None, nb_uniq_pageviews=None)
        sum_visits_length = data.get('sum_visits_length', None)
        nb_pageviews = data.get('nb_pageviews', None)
        nb_uniq_pageviews = data.get('nb_uniq_pageviews', None)
        return VisitsAnalytics(sum_visits_length=sum_visits_length, nb_pageviews=nb_pageviews, nb_uniq_pageviews=nb_uniq_pageviews)

    def resolve_sum_visits_length(self, args, context, info):
        return self.generic_resolver(args, context, info, "sum_visits_length")

    def resolve_nb_pageviews(self, args, context, info):
        return self.generic_resolver(args, context, info, "nb_pageviews")

    def resolve_nb_uniq_pageviews(self, args, context, info):
        return self.generic_resolver(args, context, info, "nb_uniq_pageviews")
