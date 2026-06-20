import requests
import config


def send_message(message):

    if not config.DISCORD_ENABLED:
        return False

    if not config.DISCORD_WEBHOOK_URL:
        return False

    try:
        response = requests.post(
            config.DISCORD_WEBHOOK_URL,
            json={
                "content": message
            },
            timeout=5
        )

        response.raise_for_status()

        return True

    except requests.exceptions.RequestException as e:
        print(f"[DISCORD ERROR] {e}")
        return False