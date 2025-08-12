from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Konfiguracja środowiska
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "malgorzata.gendlek@rtbhouse.com"
SMTP_PASS = os.environ.get("SMTP_PASS")  # uzyte app password
HELPDESK_EMAIL = "gosiage1@gmail.com"

app = App(token=SLACK_BOT_TOKEN)

# ====== helpers: widoki ======
def build_main_menu_view():
    return {
        "type": "modal",
        "callback_id": "main_menu",
        "title": {"type": "plain_text", "text": "Ticketer"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": "*What do you want to do?*"}},
            {
                "type": "actions",
                "block_id": "menu_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Send Ticket"},
                        "action_id": "menu_send_ticket"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Download TeamViewer"},
                        "action_id": "menu_download_tv"
                    },
                    {
                         "type": "button",
                         "text": {"type": "plain_text", "text": "Get VPN Config"},
                         "url": "https://get-vpn.rtbhouse.net/",
                         "action_id": "menu_get_vpn"  # unikamy Unhandled request
                     }

                ]
            }
        ],
    }

def build_tv_menu_view():
    return {
        "type": "modal",
        "callback_id": "tv_menu",
        "title": {"type": "plain_text", "text": "TeamViewer"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Choose your OS:*"}},
            {
                "type": "actions",
                "block_id": "tv_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "TeamViewer macOS"},
                        "action_id": "tv_macos"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "TeamViewer Windows"},
                        "url": "https://storage.googleapis.com/bucket_hd/TeamViewer/TeamViewer_Windows.exe"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "TeamViewer Linux"},
                        "url": "https://get.teamviewer.com/rtbhouse"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Open Ticket Form"},
                        "action_id": "global_open_ticket"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Back to Main"},
                        "action_id": "global_back_to_main"
                    }
                ]
            }
        ],
    }

def build_tv_macos_view():
    return {
        "type": "modal",
        "callback_id": "tv_macos_view",
        "title": {"type": "plain_text", "text": "TeamViewer for macOS"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Make sure to grant TeamViewer accesses* after installation (Accessibility, Screen Recording, Full Disk Access, etc.)."
                }
            },
            {
                "type": "actions",
                "block_id": "tv_macos_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Download macOS"},
                        "url": "https://storage.googleapis.com/bucket_hd/TeamViewer/TeamViewerMACOS.zip"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Open Ticket Form"},
                        "action_id": "global_open_ticket"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Back to TV Menu"},
                        "action_id": "tv_back_to_tvmenu"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Back to Main"},
                        "action_id": "global_back_to_main"
                    }
                ]
            }
        ],
    }

def build_ticket_view():
    return {
        "type": "modal",
        "callback_id": "create_ticket",
        "title": {"type": "plain_text", "text": "New Ticket"},
        "submit": {"type": "plain_text", "text": "Send"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "title_block",
                "label": {"type": "plain_text", "text": "Subject"},
                "element": {"type": "plain_text_input", "action_id": "title_input"},
            },
            {
                "type": "input",
                "block_id": "desc_block",
                "label": {"type": "plain_text", "text": "Problem description"},
                "element": {"type": "plain_text_input", "action_id": "desc_input", "multiline": True},
            },
            {
                "type": "input",
                "optional": True,
                "block_id": "files_block",
                "label": {"type": "plain_text", "text": "Attachments (optional)"},
                "element": {
                    "type": "file_input",
                    "action_id": "files_upload",
                    "filetypes": ["pdf", "jpg", "jpeg", "png", "txt", "csv", "gif"],
                    "max_files": 5
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Back to Main"},
                        "action_id": "global_back_to_main"
                    }
                ]
            }
        ],
    }

# ====== e-mail ======
def send_ticket_email(user_name, from_email, title, desc, attachments=None):
    subject = f"[SLACK] {title}"
    body = f"Ticket from {user_name} <{from_email}>:\n\nSubject: {title}\n\nDescription:\n{desc}"

    msg = MIMEMultipart()
    msg["Subject"] = subject
    # "From" = konto SMTP (autoryzacja). Nazwa widoczna jako Helpdesk (opcjonalnie).
    msg["From"] = f"Helpdesk via Slack <{SMTP_USER}>"
    msg["To"] = HELPDESK_EMAIL
    # kluczowe: odpowiedzi trafią do autora ze Slacka
    msg["Reply-To"] = from_email
    # opcjonalnie jawnie wskaż nadawcę (zgodne z RFC)
    msg["Sender"] = SMTP_USER

    msg.attach(MIMEText(body, "plain"))

    if attachments:
        for filename, file_bytes in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        # envelope sender nadal = SMTP_USER (stabilne pod DMARC)
        server.sendmail(SMTP_USER, HELPDESK_EMAIL, msg.as_string())

# ====== /hdticket: start od menu ======
@app.command("/hdticket")
def open_menu(ack, body, client):
    ack()
    client.views_open(trigger_id=body["trigger_id"], view=build_main_menu_view())

# ====== akcje menu głównego ======
@app.action("menu_send_ticket")
def handle_menu_send_ticket(ack, body, client):
    ack()
    client.views_push(trigger_id=body["trigger_id"], view=build_ticket_view())

@app.action("menu_download_tv")
def handle_menu_download_tv(ack, body, client):
    ack()
    client.views_update(view_id=body["container"]["view_id"], view=build_tv_menu_view())

# ====== TeamViewer: macOS widok i nawigacja ======
@app.action("tv_macos")
def handle_tv_macos(ack, body, client):
    ack()
    client.views_update(view_id=body["container"]["view_id"], view=build_tv_macos_view())

@app.action("tv_back_to_tvmenu")
def handle_tv_back_to_tvmenu(ack, body, client):
    ack()
    client.views_update(view_id=body["container"]["view_id"], view=build_tv_menu_view())

# ====== skróty globalne: otwarcie ticketu / powrót do main ======

@app.action("global_open_ticket")
def handle_global_open_ticket(ack, body, client):
    ack()
    client.views_push(trigger_id=body["trigger_id"], view=build_ticket_view())

@app.action("global_back_to_main")
def handle_global_back_to_main(ack, body, client):
    ack()
    client.views_update(view_id=body["container"]["view_id"], view=build_main_menu_view())

# ==== Handler do Get VPN ====
@app.action("menu_get_vpn")
def handle_menu_get_vpn(ack, body, logger):
    ack()

# ====== submit ticketu ======
@app.view("create_ticket")
def handle_submission(ack, body, client, view):
    ack()

    user_id = body["user"]["id"]
    try:
        uinfo = client.users_info(user=user_id)  # wymaga scope: users:read, users:read.email
        profile = uinfo["user"].get("profile", {}) or {}
        user_name = profile.get("real_name") or uinfo["user"].get("name") or user_id
        user_email = profile.get("email")  # <-- tu jest e-mail
    except Exception:
        user_name = user_id
        user_email = None

    title = view["state"]["values"]["title_block"]["title_input"]["value"]
    desc = view["state"]["values"]["desc_block"]["desc_input"]["value"]

    file_ids = []
    files_block_state = view["state"]["values"].get("files_block")
    if files_block_state and "files_upload" in files_block_state:
        selected_files = files_block_state["files_upload"].get("files", [])
        file_ids = [f.get("id") for f in selected_files if f.get("id")]

    attachments = []
    for fid in file_ids:
        try:
            finfo = client.files_info(file=fid)
            fobj = finfo["file"]
            fname = fobj.get("name") or fobj.get("title") or f"file_%s" % fid
            url_private = fobj.get("url_private_download") or fobj.get("url_private")
            resp = requests.get(url_private, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}, timeout=30)
            resp.raise_for_status()
            attachments.append((fname, resp.content))
        except Exception as e:
            desc += f"\n\n[UWAGA] Nie udało się pobrać załącznika {fid}: {e}"

    try:
        # fallback: jeśli brak maila w profilu, użyj konta SMTP jako Reply-To
        from_email = user_email or SMTP_USER
        send_ticket_email(user_name, from_email, title, desc, attachments)
        confirmation = f"✅ The request has been submitted to the helpdesk.\nSubject: {title}\nDescription: {desc}"
    except Exception as e:
        confirmation = f"❌ Error while sending the email: {str(e)}"

    client.chat_postMessage(channel=user_id, text=confirmation)

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
