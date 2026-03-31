# Setup Guide: Connecting NextRole AI

Follow these steps to connect your Real Gmail and Telegram bot to the system.

## 1. Create a Telegram Bot
1.  Open Telegram and search for **@BotFather**.
2.  Send `/newbot` and follow the instructions to name your bot.
3.  **Copy the API Token** (e.g., `123456789:ABCDefgh...`). This is your `TELEGRAM_BOT_TOKEN`.
4.  (Optional) Set a description and user profile picture for your bot.

---

## 2. Configure Google Cloud (Gmail API)
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a **New Project** (e.g., "NextRole-AI").
3.  Go to **APIs & Services > Library** and search for **Gmail API**. Click **Enable**.
4.  Go to **APIs & Services > OAuth Consent Screen**:
    - Select **External**.
    - Fill in the required App Name and User Support Email.
    - Add the scope: `https://www.googleapis.com/auth/gmail.modify`.
    - Add your own email as a **Test User**.
5.  Go to **APIs & Services > Credentials**:
    - Click **Create Credentials > OAuth Client ID**.
    - Select **Web Application**.
    - Add an **Authorized Redirect URI**: `http://localhost:8000/gmail/oauth/callback` (or your ngrok URL if testing remotely).
    - **Copy the Client ID and Client Secret**.

---

## 3. Local Tunneling (NGROK)
Since the system uses webhooks for Telegram and Google OAuth, you need a public URL if you're running locally.
1.  Download and install [ngrok](https://ngrok.com/).
2.  Run: `ngrok http 8000`.
3.  **Copy the Forwarding URL** (e.g., `https://a1b2-c3d4.ngrok-free.app`). This will be your `TELEGRAM_BASE_URL`.

---

## 4. Finalize Environment Variables
Create a file named **`.env`** in the `backend/` folder and paste the following, replacing the placeholders with your keys:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_WEBHOOK_SECRET=a_random_string_here
TELEGRAM_BASE_URL=https://your-ngrok-url.ngrok-free.app

# Google OAuth
GMAIL_OAUTH_CLIENT_ID=your_client_id_here
GMAIL_OAUTH_CLIENT_SECRET=your_client_secret_here
GMAIL_OAUTH_REDIRECT_URL=https://your-ngrok-url.ngrok-free.app/gmail/oauth/callback

# Security
ENCRYPTION_KEY= (run 'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"')
DATABASE_URL=sqlite:///./nextrole.db
ENVIRONMENT=development
```

---

## 5. Launch and Connect
1.  Run **`start.bat`** from the root folder.
2.  Open your Telegram bot and send **`/start`**.
3.  Follow the instruction: **`connect gmail`**.
4.  Click the link, authorize with your Google account, and you're all set!
