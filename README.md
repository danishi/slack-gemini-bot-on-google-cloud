# Slack Gemini Bot on Google Cloud

This repository provides a Slack bot backend implemented in Python that uses [Slack Bolt](https://slack.dev/bolt-python) and Google Cloud's [Vertex AI Gemini](https://cloud.google.com/vertex-ai) model via the [google-genai](https://pypi.org/project/google-genai/) SDK. The bot responds to text or image messages and maintains conversation context within Slack threads. It is designed to run on [Cloud Run](https://cloud.google.com/run).

## Features
- Responds to `@mention` messages in Slack channels.
- Supports text and image inputs from Slack messages. Images are fetched via authenticated URLs and sent to Gemini for multimodal understanding.
- Maintains conversation context by retrieving prior messages in a thread and sending them as conversation history to Gemini.
- FastAPI-based web server suitable for Cloud Run.
- Deployment script for building and deploying to Cloud Run.

## Project Structure
```
app/
  main.py           # FastAPI app and Slack Bolt handlers
scripts/
  deploy.sh         # Helper script to deploy to Cloud Run
Dockerfile           # Container definition for Cloud Run
requirements.txt     # Python dependencies
```

## Prerequisites
- Python 3.13
- [Google Cloud SDK](https://cloud.google.com/sdk) with `gcloud` authenticated
- Slack workspace admin privileges

## Local Development
1. Install dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Configure environment variables
   ```bash
   cp .env.example .env
   # edit .env and set your Slack and Google Cloud credentials
   ```
3. Run the server
   ```bash
   uvicorn app.main:fastapi_app --host 0.0.0.0 --port 8080 --reload
   ```
4. Use a tunneling tool like `ngrok` to expose `http://localhost:8080/slack/events` to Slack during development.

## Slack App Configuration
1. Create a new Slack app at <https://api.slack.com/apps>.
2. Under **OAuth & Permissions**, add the following Bot Token scopes:
   - `app_mentions:read`
   - `chat:write`
   - `channels:history`
   - `groups:history`
   - `im:history`
   - `mpim:history`
   - `files:read`
3. Install the app to your workspace to obtain `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET`.
4. Enable **Event Subscriptions** and set the Request URL to `https://<your-cloud-run-service-url>/slack/events`.
5. Subscribe to bot events: `app_mention`.
6. Invite the bot to channels where you want to use it.

## Deploy to Cloud Run
The repository includes a helper script to build the container and deploy to Cloud Run. Ensure your `.env` contains `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` before running:

```bash
./scripts/deploy.sh
```

The script will:
1. Build the container image using Cloud Build.
2. Deploy the image to Cloud Run.
3. Set the required environment variables on the service.

After deployment, configure the Slack app's event subscription URL to the Cloud Run service URL.

## License
[Apache-2.0](LICENSE)
