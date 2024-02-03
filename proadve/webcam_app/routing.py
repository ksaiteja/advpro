
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from proadve.webcam_app.consumer import AdvertisementConsumer
# from webcam_app.consumers import AdvertisementConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/advertisement/", AdvertisementConsumer.as_asgi()),
        ]),
    ),
})
