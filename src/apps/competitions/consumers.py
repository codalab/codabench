import json
import os

import aiofiles
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from competitions.models import Submission


class SubmissionIOConsumer(AsyncWebsocketConsumer):
    #
    async def connect(self):
        submission_id = self.scope['url_route']['kwargs']['submission_id']
        secret = self.scope['url_route']['kwargs']['secret']
        try:
            Submission.objects.get(pk=submission_id, secret=secret)
        except Submission.DoesNotExist:
            return await self.close()

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        user_pk = self.scope['url_route']['kwargs']['user_pk']
        submission_id = self.scope['url_route']['kwargs']['submission_id']
        submission_output_path = os.path.join(settings.TEMP_SUBMISSION_STORAGE, f"{submission_id}.txt")
        os.makedirs(os.path.dirname(submission_output_path), exist_ok=True)

        async with aiofiles.open(submission_output_path, 'a+') as f:
            await f.write(f'{text_data}\n')

        await self.channel_layer.group_send(f"submission_listening_{user_pk}", {
            'type': 'submission.message',
            'text': json.loads(text_data),
            'submission_id': submission_id,
        })
        # TODO! Refuse to write to file after 10MB has been received ???


class SubmissionOutputConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            return await self.close()

        await self.accept()
        await self.channel_layer.group_add(f"submission_listening_{self.scope['user'].pk}", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(f"submission_listening_{self.scope['user'].pk}", self.channel_name)
        await self.close()

    def group_send(self, text, submission_id, full_text=False):
        return self.channel_layer.group_send(f"submission_listening_{self.scope['user'].pk}", {
            'type': 'submission.message',
            'text': text,
            'submission_id': submission_id,
            'full_text': full_text,
        })

    async def receive(self, text_data=None, bytes_data=None):
        """We expect to receive a message at this endpoint containing the ID(s) of submissions to get
        details about; typically on page load, looking up the previous submission details"""
        data = json.loads(text_data)

        submission_ids = data.get("submission_ids", [])

        if submission_ids:
            # Filter out submissions not by this user
            submissions = Submission.objects.filter(id__in=submission_ids, owner=self.scope["user"]).values_list('pk', flat=True)

            for sub_id in submissions:
                text_path = os.path.join(settings.TEMP_SUBMISSION_STORAGE, f"{sub_id}.txt")
                if os.path.exists(text_path):
                    with open(text_path) as f:
                        text = f.read()
                    await self.group_send(text, sub_id, full_text=True)

    async def submission_message(self, event):
        data = {
            "type": "catchup" if event.get('full_text') else "message",
            "submission_id": event['submission_id'],
            "data": event['text']
        }
        await self.send(json.dumps(data))
