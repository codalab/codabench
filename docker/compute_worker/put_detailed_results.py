import argparse
import asyncio
import json

import requests
import websockets

parser = argparse.ArgumentParser()
parser.add_argument(
    'url',
    type=str,
    help='The URL to send the detailed results to'
)
parser.add_argument(
    'file_path',
    type=str,
    help='File path to the detailed_results.html file'
)
parser.add_argument(
    'websocket_url',
    type=str,
    help='URL for websocket to communicate with the frontend about updates to the detailed results'
)

args = parser.parse_args()


async def update_frontend():
    async with websockets.connect(args.websocket_url) as websocket:
        await websocket.send(json.dumps({
            "kind": 'detailed_result',
        }))


with open(args.file_path, 'rb') as f:
    resp = requests.put(
        args.url,
        data=f,
        headers={
            'x-ms-blob-type': 'BlockBlob',
            'x-ms-version': '2018-03-28',
        }
    )

asyncio.get_event_loop().run_until_complete(update_frontend())
