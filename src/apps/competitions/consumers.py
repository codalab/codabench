import json
import os

import aiofiles

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings


class SubmissionIOConsumer(AsyncWebsocketConsumer):
    #
    async def connect(self):
        # Check submission secret perms here?
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        # await self.send({
        #     "type": "websocket.send",
        #     "text": text_data,
        # })

        # TODO! Get actual submission ID via router url path jazz
        # TODO! We will have to synchronously check in database what submission ID -> secret is to do proper write
        # Maybe we can just write to a submission_<secret>.txt file
        # However, we need to limit

        kind = json.loads(text_data).get('kind')

        submission_id = self.scope['url_route']['kwargs']['submission_id']
        if kind != 'status_update':
            submission_output_path = os.path.join(settings.TEMP_SUBMISSION_STORAGE, f"{submission_id}.txt")
            os.makedirs(os.path.dirname(submission_output_path), exist_ok=True)

            async with aiofiles.open(submission_output_path, 'a+') as f:
                await f.write(f'{text_data}\n')

        # TODO: Await to broadcast to everyone listening to this submission key or whatever
        await self.channel_layer.group_send("submission_listening", {
            'type': 'submission.message',
            'text': text_data,
            'submission_id': submission_id,
        })
        # TODO! Refuse to write to file after 10MB has been received ???


class SubmissionOutputConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("submission_listening", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("submission_listening", self.channel_name)
        await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        submission_id = text_data
        text_path = os.path.join(settings.TEMP_SUBMISSION_STORAGE, f"{submission_id}.txt")
        if os.path.exists(text_path):
            with open(text_path) as f:
                text = f.read()
            await self.channel_layer.group_send("submission_listening", {
                'type': 'submission.message',
                'text': text,
                'submission_id': submission_id,
                'full_text': True,
            })

    async def submission_message(self, event):
        data = {
            "type": "catchup" if event.get('full_text') else "message",
            "submission_id": event['submission_id'],
            "data": event['text']
        }
        await self.send(json.dumps(data))
