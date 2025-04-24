import os, json, time, hmac, hashlib
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai, requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

app = Flask(__name__)

# Config
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_CHANNEL = os.getenv("OUTPUT_CHANNEL")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

openai.api_key = OPENAI_API_KEY

# Google Sheets

def store_prompt(prompt, score, user):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    sheet = gspread.authorize(creds).open(GOOGLE_SHEET_NAME).sheet1
    sheet.append_row([time.strftime('%Y-%m-%d %H:%M:%S'), user, prompt, score])

# Verify Slack requests

def verify_signature(request):
    timestamp = request.headers['X-Slack-Request-Timestamp']
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False

    sig_basestring = f"v0:{timestamp}:{request.get_data(as_text=True)}"
    my_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    slack_signature = request.headers['X-Slack-Signature']
    return hmac.compare_digest(my_signature, slack_signature)

# Generate prompt

def generate_prompt(input_text):
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful AI prompt generator."},
            {"role": "user", "content": input_text}
        ]
    )
    return res["choices"][0]["message"]["content"].strip()

# Score prompt

def score_prompt(prompt):
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Rate this prompt from 1 (poor) to 5 (excellent) based on usefulness and clarity."},
            {"role": "user", "content": prompt}
        ]
    )
    return res["choices"][0]["message"]["content"].strip()

# Send Slack message with button

def post_to_slack(prompt, score, user, original_text):
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Generated Prompt:*\n{prompt}\n\n*Score:* {score}/5"}
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Regenerate"},
                    "value": json.dumps({"text": original_text, "user": user}),
                    "action_id": "regenerate_prompt"
                }
            ]
        }
    ]
    requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={"channel": OUTPUT_CHANNEL, "blocks": blocks, "text": prompt}
    )

@app.route("/slack/events", methods=["POST"])
def slack_events():
    if not verify_signature(request):
        return "Invalid signature", 400

    data = request.json

    # URL verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    # Button click (block actions)
    if data.get("type") == "block_actions":
        action = data["actions"][0]
        payload = json.loads(action["value"])
        prompt = generate_prompt(payload["text"])
        score = score_prompt(prompt)
        store_prompt(prompt, score, payload["user"])
        post_to_slack(prompt, score, payload["user"], payload["text"])
        return "", 200

    # Message event
    if "event" in data:
        event = data["event"]
        if event.get("type") == "message" and "subtype" not in event:
            input_text = event.get("text")
            user = event.get("user")
            prompt = generate_prompt(input_text)
            score = score_prompt(prompt)
            store_prompt(prompt, score, user)
            post_to_slack(prompt, score, user, input_text)

    return "", 200
