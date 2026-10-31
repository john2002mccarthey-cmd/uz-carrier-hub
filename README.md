# UZ CARRIER HUB — Telegram bot MVP

## Included
- Uzbek, Russian and English registration flow
- Registers truck owners, transport companies and drivers
- Captures phone, vehicle type, payload, body type, location, routes and availability
- Admin notifications with Verify / Reject buttons
- Admin commands: `/stats`, `/pending`, `/search <term>`, `/export`
- SQLite CRM database; re-registration updates the same Telegram profile

## Setup
1. In Telegram, open **@BotFather**, send `/newbot`, follow the prompts and copy the token.
2. Find your numeric Telegram user ID using a trusted ID utility. Put it in `ADMIN_IDS`.
3. Install Python 3.10+.
4. In this folder run:
   ```bash
   python -m venv .venv
   # Windows: .venv\\Scripts\\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
5. Put your token and numeric ID in `.env`.
6. Start the bot:
   ```bash
   python -m app.bot
   ```

## Admin commands
- `/stats` — counts
- `/pending` — latest pending registrations
- `/search term` — search profiles
- `/export` — download CSV

## Notes
- This is a working MVP source package, not yet deployed or connected to a live Telegram bot.
- Keep `.env` private. Never share the bot token.
- Data is stored in local SQLite. Back up `carriers.sqlite3`.
- Ask users for consent before collecting and using their phone/location details.
- Verify identity, truck documents, authority to transport, insurance and applicable permits before assigning loads.
- GPS tracking, load booking, payments and automatic Google Sheets sync are not included yet.
