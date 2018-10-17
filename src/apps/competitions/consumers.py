import aiofiles
import os

from channels.consumer import AsyncConsumer
from tempfile import gettempdir


class SubmissionInputConsumer(AsyncConsumer):

    # async def websocket_connect(self, event):
    #     await self.send({
    #         "type": "websocket.accept",
    #     })
    #
    #     # TODO! On connection, send contents of the temp file, if any, so they can get caught up

    async def websocket_receive(self, event):
        await self.send({
            "type": "websocket.send",
            "text": event["text"],
        })

        # TODO! Get actual submission ID via router url path jazz
        # TODO! Shit. We will have to synchronously check in database what submission ID -> secret is to do proper write
        # Maybe we can just write to a submission_<secret>.txt file
        # However, we need to limit

        submission_id = 50
        submission_output_path = f"/codalab_tmp/{submission_id}.txt"
        print(f"opening {submission_output_path}")
        async with aiofiles.open(submission_output_path, 'a+') as f:
            await f.write(event["text"])
            print(f"writing {event['text']}")


            # TODO: Await to broadcast to everyone listening to this submission key or whatever
            await self.channel_layer.group_send("submission_listening", {
                'type': 'websocket.send',
                'text': event["text"]
            })

        # TODO! Refuse to write to file after 10MB has been received ???


class SubmissionOutputConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        # TODO! On connection, send contents of the temp file, if any, so they can get caught up
        print("OOOOOOOOKAY")

        await self.channel_layer.group_add("submission_listening", self.channel_name)
        # await self.accept()  # TODO: why is this needed?
        await self.send({
            "type": "websocket.accept",
        })


    async def websocket_disconnect(self, event):
        await self.channel_layer.group_discard("submission_listening", self.channel_name)
        # await self.close()

    # async def websocket_receive(self, event):
    #     pass
