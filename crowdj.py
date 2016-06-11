from flask import Flask, request, redirect
import twilio.twiml
from twilio.rest import TwilioRestClient
from datetime import datetime as dt
import time
import json
import os

import sqlite3


ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]

client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

app = Flask(__name__)


conn = sqlite3.connect('my_hits.db')
c = conn.cursor()


start_time = None
sesh_id = None

result = {
    "hot": 0,
    "cold": 0,
    "sesh_id": sesh_id
}


def analyze_messages(messages, sesh_id):
    for msg in messages:
        if msg.direction == "inbound":
            if msg.date_created > start_time:
                if "hot" in msg.body.lower():
                    result['hot'] += 1
                elif "cold" in msg.body.lower():
                    result['cold'] += 1
    return result


@app.route("/submit/", methods=['GET', 'POST'])
def submit(sesh_id=None):
    resp = twilio.twiml.Response()
    resp.message(
        "Thanks for your input! - as always, this next one's for you!")
    return str(resp)


@app.route("/start_poll/<session_id>/", methods=['GET', 'POST'])
def start_poll(session_id=None):
    sesh_id = session_id
    start_time = dt.utcnow()

    for i in range(start_time):
        c.execute(
            'CREATE TABLE IF NOT EXISTS TableOfMusic (sesh_id REAL, hot REAL, cold REAL);')
        c.execute('INSERT INTO TableOfMusic (sesh_id, hot, cold) VALUES (result['sesh_id'], result['hot'], result['cold']);')
        time.sleep(1)
    conn.commit()
    c.close()
    conn.close()

    return sesh_id


@app.route("/get_results/", methods=['GET', 'POST'])
def get_results():
    # get all messages from today
    messages = client.messages.list()
    c.execute("SELECT a.* FROM TableOfMusic a LEFT OUTER JOIN TableOfMusic b ON a.sesh_id < b.sesh_id WHERE b.sesh_id IS NULL;")
    if start_poll(sesh_id) and start_time:
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
    # global start_time
    # global sesh_id
    start_time = None
    sesh_id = None
    return "Stopped"


if __name__ == "__main__":
    app.run(debug=True)
