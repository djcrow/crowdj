from flask import Flask, request, redirect
import twilio.twiml
from twilio.rest import TwilioRestClient
from datetime import datetime as dt
import json
import os
import requests


ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]

client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

app = Flask(__name__)

global start_time
global sesh_id

start_time = None
sesh_id = None


def analyze_messages(messages, sesh_id):
    hot = 0
    cold = 0
    for msg in messages:
        if msg.direction == "inbound":
            if msg.date_created > start_time:
                r = requests.post("http://text-processing.com/api/sentiment",
                                  "text={}".format(msg.body))
                label = json.loads(r.json())['label']
                if label == 'pos':
                    hot += 1
                elif label == 'neg':
                    cold += 1
    result = {
        "hot": hot,
        "cold": cold,
        "sesh_id": sesh_id
    }
    return result


@app.route("/submit/", methods=['GET', 'POST'])
def submit(sesh_id=None):
    resp = twilio.twiml.Response()
    resp.message("Thanks for your input! ")
    return str(resp)


@app.route("/start_poll/<session_id>/", methods=['GET', 'POST'])
def start_poll(session_id=None):
    global start_time
    global sesh_id
    sesh_id = session_id
    start_time = dt.utcnow()
    return sesh_id


@app.route("/get_results/", methods=['GET', 'POST'])
def get_results():
    # print sesh_id
    # print start_time
    # get all messages from today
    messages = client.messages.list()
    if sesh_id and start_time:
        result = analyze_messages(messages, sesh_id)
        return json.dumps(result)
    else:
        return "Please establish session"


@app.route("/stop_poll/", methods=['GET', 'POST'])
def stop_poll():
    # Delete all messages from today
    messages = client.messages.list(date_sent=dt.utcnow())
    for msg in messages:
        client.messages.delete(msg.sid)

    # Reset start time and sesh_id
    global start_time
    global sesh_id
    start_time = None
    sesh_id = None
    return "Stopped"


if __name__ == "__main__":
    app.run(debug=True)
