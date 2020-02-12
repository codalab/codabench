import argparse

import requests

parser = argparse.ArgumentParser()
parser.add_argument('url', type=str, help='The URL to send the detailed results to')
parser.add_argument('file_path', type=str, help='File path to the detailed_results.html file')

args = parser.parse_args()

with open(args.file_path, 'rb') as f:
    resp = requests.put(
        args.url,
        data=f,
        headers={
            'x-ms-blob-type': 'BlockBlob',
            'x-ms-version': '2018-03-28',
        }
    )
    print(resp.content)
    print(resp.status_code)
