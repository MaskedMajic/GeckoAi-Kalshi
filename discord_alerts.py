import requests
import config


def send_message(message):

    if not config.DISCORD_ENABLED:
        return

    if not config.DISCORD_WEBHOOK_URL:
        return

    requests.post(
        config.DISCORD_WEBHOOK_URL,
        json={
            "content": message
        }
    )