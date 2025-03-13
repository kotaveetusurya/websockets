"""
ASGI config for wstest1 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import wsapp.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wstest1.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(wsapp.routing.websocket_urlpatterns)
    ),  # Add your WebSocket application's URL patterns here.
})
