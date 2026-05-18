# from django.conf import settings
# from typing import Any, Dict, List

# def get_context_environment_for_templates() -> Dict[str, Any]:
#     """
#     Get settings variables for templates.
#     """
#     return {
#         "debug": settings.DEBUG,
#         "SOCKETIO_HOST": settings.SOCKETIO_HOST,
#         "SOCKETIO_PORT": settings.SOCKETIO_PORT,
#         "TIME_ZONE": settings.TIME_ZONE,
#         "M2M_URI": settings.M2M_URL,
#         "M2M_TOKEN": settings.M2M_TOKEN,
#         "WWW_HOST": settings.WWW_HOST,
#         "ENTERPRISES_HOST": settings.ENTERPRISES_HOST,
#         "REPORT_HOST": settings.REPORT_HOST,
#         "STATIC_VERSION": settings.STATIC_VERSION,
#         "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
#         "USE_HTTPS": settings.USE_HTTPS,
#         "ENTERPRISE_WHIT_DANGER_ZONE": settings.ENTERPRISE_WHIT_DANGER_ZONE,
#         "ENTERPRISE_WHIT_LOGO": settings.ENTERPRISE_WHIT_LOGO,
#         "MEDIA_URL": settings.MEDIA_URL,
#         "DOMAIN_PORT": ":8000" if settings.DEBUG else ""
#     }


# def send_email(
#         subject='', to=[], template_name='', context={}, tags=[],
#         attachments=None, metadata={}, track_clicks=False,
#         track_opens=False, esp_extra={}, merge_data={}, cc=None,
#         from_email=settings.DEFAULT_FROM_EMAIL):

#     """
#         Sends email with AnyMail
#     """
#     try:
#         context.update(get_context_environment_for_templates())
#         html_content = render_to_string(
#             'email/%s.html' % template_name, context)
#         text_content = strip_tags(html_content)
#         msg = AnymailMessage(
#             subject=subject, body=text_content, from_email=from_email, to=to,
#             tags=tags, metadata=metadata, track_clicks=track_clicks,
#             track_opens=track_opens, esp_extra=esp_extra,
#             merge_data=merge_data, cc=cc)
#         msg.attach_alternative(html_content, 'text/html')
#         if attachments is not None:
#             for attachment in attachments:
#                 msg.attach(
#                     filename=attachment['filename'],
#                     content=attachment['content'])
#         msg.send()
#     except Exception:
#         client.captureException()
