# webcam_app/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AdvertisementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "advertisement_group",
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "advertisement_group",
            self.channel_name,
        )

    async def send_advertisement_update(self, event):
        advertisement_path = event["advertisement_path"]
        await self.send(text_data=json.dumps({
            'advertisement_path': advertisement_path,
        }))
