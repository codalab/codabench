import json
import time

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.exceptions import DenyConnection
from django_redis import get_redis_connection
from competitions.models import Submission
from utils.data import make_url_sassy

import logging
logger = logging.getLogger(__name__)


class SubmissionIOConsumer(AsyncWebsocketConsumer):
    #
    async def connect(self):
        submission_id = self.scope['url_route']['kwargs']['submission_id']
        secret = self.scope['url_route']['kwargs']['secret']
        logger.debug(f"CONSUMER_MARKER: Connecting for submission {submission_id} with secret {secret}")
        try:
            _ = await sync_to_async(Submission.objects.get)(
                pk=submission_id, secret=secret
            )
        except Submission.DoesNotExist:
            return await self.close()

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        user_pk = self.scope['url_route']['kwargs']['user_pk']
        submission_id = self.scope['url_route']['kwargs']['submission_id']
        logger.debug(f"CONSUMER_MARKER: Received data for submission {submission_id} | {text_data}")

        try:
            # Get all necessary data in one transaction if possible
            sub = await sync_to_async(Submission.objects.get)(pk=submission_id)
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(pk=user_pk)
            phase = await sync_to_async(lambda: sub.phase)()
            competition = await sync_to_async(lambda: phase.competition)()
            has_admin = await sync_to_async(lambda: competition.user_has_admin_permission(user))()

            if phase.hide_output and not has_admin:
                logger.warning(f"User {user_pk} attempted to access hidden output for submission {submission_id}")
                return

            data = json.loads(text_data)

            if data['kind'] == 'detailed_result_update':
                # No need to fetch the submission again, we already have it
                data['result_url'] = make_url_sassy(sub.detailed_result.name)
                # update text data to include the newly added sas url for retrieval on page refresh
                text_data = json.dumps(data)

            # Store in Redis
            con = get_redis_connection("default")
            con.append(f':1:submission-{submission_id}-log', f'{text_data}\n')

            # Send to channel layer
            try:
                await self.channel_layer.group_send(f"submission_listening_{user_pk}", {
                    'type': 'submission_message',
                    'text': data,
                    'submission_id': submission_id,
                })
                logger.debug(f"RELAY_MARKER: Sent message to channel layer for user {user_pk}, submission {submission_id}")
            except Exception as e:
                logger.error(f"Error sending to channel layer: {e}")

        except Submission.DoesNotExist:
            logger.warning(f"Submission {submission_id} does not exist")
            await self.close(code=4004)  # Custom code for "Resource not found"
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {e}")
            await self.close(code=1011)  # Internal error


class SubmissionOutputConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            return await self.close()
            # raise DenyConnection()

        try:
            await self.accept()
            logger.debug(f"WebSocket connected for user {self.scope['user'].pk}")
        except RuntimeError as e:
            logger.error(f"WebSocket accept failed: {e}")
            return  # prevent group_add

        await self.channel_layer.group_add(f"submission_listening_{self.scope['user'].pk}", self.channel_name)
        logger.debug(f"WebSocket connection established for user {self.scope['user'].pk}")

        # Send confirmation to client that the connection is ready
        await self.send(json.dumps({
            "type": "connection_ready",
            "status": "connected"
        }))

    async def disconnect(self, close_code):
        logger.debug(f"WebSocket disconnecting with code {close_code} for user {self.scope['user'].pk}")
        try:
            await self.channel_layer.group_discard(f"submission_listening_{self.scope['user'].pk}", self.channel_name)
        except Exception as e:
            logger.error(f"Error during group_discard: {e}")

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
            # submissions = Submission.objects.filter(id__in=submission_ids, owner=self.scope["user"])
            submissions = await sync_to_async(lambda: list(Submission.objects.filter(
                id__in=submission_ids, owner=self.scope["user"]
            )))()
            con = get_redis_connection("default")

            for sub in submissions:
                text = (con.get(f':1:submission-{sub.id}-log'))
                if text:
                    await self.group_send(text.decode('utf-8'), sub.id, full_text=True)

    async def submission_message(self, event):
        logger.debug(f"FRONTEND_MARKER: Processing message for submission {event['submission_id']}")

        time.sleep(0.3)  # Simulate some processing delay
        data = {
            "type": "catchup" if event.get('full_text') else "message",
            "submission_id": event['submission_id'],
            "data": event['text']
        }

        try:
            await self.send(json.dumps(data))
            logger.debug(f"FRONTEND_MARKER: Successfully sent message to frontend for submission {event['submission_id']}")
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
