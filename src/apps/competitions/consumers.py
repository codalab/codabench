import aiofiles

from channels.generic.websocket import AsyncWebsocketConsumer


class SubmissionIOConsumer(AsyncWebsocketConsumer):
    #
    # async def connect(self):
    #     print("joinin group")
    #     await self.channel_layer.group_add(
    #         "submission_listening",
    #         self.channel_name
    #     )
    #     await self.accept()
    #     # TODO! On connection, send contents of the temp file, if any, so they can get caught up
    #
    # async def disconnect(self, close_code):
    #     print("leavin group")
    #     await self.channel_layer.group_discard(
    #         "submission_listening",
    #         self.channel_name
    #     )
    #     await self.close(close_code)

    async def receive(self, text_data=None, bytes_data=None):
        # await self.send({
        #     "type": "websocket.send",
        #     "text": text_data,
        # })

        # TODO! Get actual submission ID via router url path jazz
        # TODO! Shit. We will have to synchronously check in database what submission ID -> secret is to do proper write
        # Maybe we can just write to a submission_<secret>.txt file
        # However, we need to limit

        submission_id = 50
        submission_output_path = f"/codalab_tmp/{submission_id}.txt"
        print(f"opening {submission_output_path}")
        async with aiofiles.open(submission_output_path, 'a+') as f:
            await f.write(text_data)
            print(f"writing {text_data}")
            print(f"{type(text_data)}")

        # print(f"We DO have it {getattr(self, 'submission_message', None)}")

        # TODO: Await to broadcast to everyone listening to this submission key or whatever
        await self.channel_layer.group_send("submission_listening", {
            'type': 'submission.message',
            'text': text_data,
        })

        # TODO! Refuse to write to file after 10MB has been received ???


class SubmissionOutputConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print("Hey, we're trying to connect2")
        # TODO! On connection, send contents of the temp file, if any, so they can get caught up

        print(self.channel_name)

        # import ipdb; ipdb.set_trace()

        await self.accept()
        await self.channel_layer.group_add("submission_listening", self.channel_name)
        # await self.send(text_data="Opening test msg")
        # print("Tried to send text?")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("submission_listening", self.channel_name)
        await self.close()

    # async def websocket_receive(self, event):
    #     pass

    async def submission_message(self, event):
        await self.send(event['text'])
#
#
# class SubmissionOutputConsumer(AsyncConsumer):
#
#     async def websocket_connect(self, event):
#         # TODO! On connection, send contents of the temp file, if any, so they can get caught up
#         print("OOOOOOOOKAY")
#
#         await self.channel_layer.group_add("submission_listening", self.channel_name)
#         # await self.accept()  # TODO: why is this needed?
#         await self.send({
#             "type": "websocket.accept",
#         })
#
#
#     async def websocket_disconnect(self, event):
#         await self.channel_layer.group_discard("submission_listening", self.channel_name)
#         # await self.close()
#
#     # async def websocket_receive(self, event):
#     #     pass
