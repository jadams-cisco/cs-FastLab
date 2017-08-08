from waitress import serve
from flask import Flask

import requests

app = Flask(__name__)

@app.route('/alert')
def alert():
    #Send message to the alert spark room

    url = "https://api.ciscospark.com/v1/messages"
    payload = """{
        "roomId":"Y2lzY29zcGFyazovL3VzL1JPT00vOTUxMzJkYjAtN2M0MS0xMWU3LWJiOWQtNDM4ODViZDVlZjgw",
        "text":"FastLab API has encountered a critical error!"
    }"""

    headers = {
        'content-type': "application/json",
        'authorization': "Bearer NWJiMmVlNTQtYmRmNi00ZGNlLTg3ZmMtMWYwMWRlNWQ0MGQ1NjkyYzNkNmItZGNi"
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    return response.text

serve(app, host="0.0.0.0", port='8080')