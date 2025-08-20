import os
import asyncio
from typing import List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi import AsyncSlackRequestHandler
from google import genai
from google.genai import types

# Environment variables
load_dotenv()
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
PROJECT_ID = os.environ.get("GOOGLE_PROJECT")
LOCATION = os.environ.get("GOOGLE_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

# Initialize Slack Bolt AsyncApp
bolt_app = AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
handler = AsyncSlackRequestHandler(bolt_app)

fastapi_app = FastAPI()

async def _build_contents_from_thread(client, channel: str, thread_ts: str) -> List[types.Content]:
    """Fetch thread messages and build google-genai contents."""
    history = await client.conversations_replies(channel=channel, ts=thread_ts, limit=50)
    contents: List[types.Content] = []
    async with httpx.AsyncClient() as http_client:
        for msg in history["messages"]:
            role = "model" if msg.get("bot_id") else "user"
            parts = []
            text = msg.get("text")
            if text:
                parts.append(types.Part.from_text(text))
            for f in msg.get("files", []):
                mimetype = f.get("mimetype", "")
                if mimetype.startswith("image/"):
                    url = f.get("url_private_download")
                    if url:
                        resp = await http_client.get(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"})
                        resp.raise_for_status()
                        parts.append(types.Part.from_bytes(resp.content, mime_type=mimetype))
            if parts:
                contents.append(types.Content(role=role, parts=parts))
    return contents

@bolt_app.event("app_mention")
async def handle_mention(body, say, client, logger):
    event = body["event"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts") or event["ts"]

    contents = await _build_contents_from_thread(client, channel, thread_ts)

    def call_gemini() -> str:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        response = genai_client.models.generate_content(model=MODEL_NAME, contents=contents)
        return response.text

    try:
        reply_text = await asyncio.to_thread(call_gemini)
    except Exception as e:
        logger.exception("Gemini call failed")
        reply_text = f"Error from Gemini: {e}"

    await say(reply_text, thread_ts=thread_ts)

@fastapi_app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

@fastapi_app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:fastapi_app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
