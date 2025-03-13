from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/socket-server/(?P<room_slug>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/chat/private/(?P<user1>\w+)/(?P<user2>\w+)/(?P<room_slug>[-\w]+)/$', consumers.PrivateChatConsumer.as_asgi()),
    re_path(r'ws/global-unread/', consumers.GlobalUnreadConsumer.as_asgi()),
]