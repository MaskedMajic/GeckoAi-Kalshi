import os
import sys
from pathlib import Path


ENV_PATH = ".env"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress ENTER to continue...")


def env_exists():
    return os.path.exists(ENV_PATH)


def write_env(values):
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")


def ask_required(prompt):
    while True:
        value = input(prompt).strip().strip('"')

        if value:
            return value

        print("❌ Required. Try again.\n")


def ask_pem_path():
    while True:
        print("\nPaste PEM path or drag the .pem file here:")
        path = input("> ").strip().strip('"')

        if os.path.exists(path):
            print("✅ PEM found.")
            return path

        print("❌ File not found. Try again.")


def ask_mode():
    while True:
        print("\nTrading Mode")
        print("[1] Paper")
        print("[2] Live")

        choice = input("> ").strip()

        if choice == "1":
            return "paper"

        if choice == "2":
            return "live_test"

        print("❌ Pick 1 or 2.")


def first_run_setup():
    clear()

    print("==============================")
    print("      GECKOAI SETUP")
    print("==============================\n")

    print("No config found. Let's set it up.\n")

    key_id = ask_required("Paste Kalshi API Key ID:\n> ")
    pem_path = ask_pem_path()
    mode = ask_mode()

    values = {
        "BOT_VERSION": "0.3.0",
        "MODE": mode,
        "SIZING_MODE": "balance_step",
        "STARTING_BANKROLL": "5",
        "MIN_BANKROLL": "1",
        "FIXED_CONTRACTS": "1",
        "MAX_CONTRACTS": "50",
        "LIVE_MAX_CONTRACTS": "10",
        "ENTRY_MIN": "0.87",
        "ENTRY_MAX": "0.95",
        "MAX_TIME_LEFT_MINUTES": "6",
        "DISCORD_ENABLED": "False",
        "DISCORD_WEBHOOK_URL": "",
        "GLOBAL_STATS_ENABLED": "True",
        "GLOBAL_LIVE_ONLY": "True",
        "GLOBAL_STATS_URL": "",
        "SHARE_BALANCE": "True",
        "SHARE_TRADE_LOGS": "True",
        "KALSHI_KEY_ID": key_id,
        "KALSHI_PRIVATE_KEY_PATH": pem_path,
        "ENABLE_LOGS": "True",
    }

    clear()

    print("==============================")
    print("      CONFIRM CONFIG")
    print("==============================\n")

    print(f"Mode: {mode}")
    print(f"API Key: {'*' * max(0, len(key_id) - 4)}{key_id[-4:]}")
    print(f"PEM: {pem_path}")
    print("\nSave config?")

    confirm = input("[Y/N] > ").strip().lower()

    if confirm != "y":
        print("Setup cancelled.")
        sys.exit()

    write_env(values)

    print("\n✅ Config saved to .env")
    pause()


def menu():
    while True:
        clear()

        print("==============================")
        print("      GECKOAI KALSHI")
        print("==============================\n")

        print("[1] Start Bot")
        print("[2] Configure Bot")
        print("[3] Exit\n")

        choice = input("> ").strip()

        if choice == "1":
            clear()
            import main
            return

        if choice == "2":
            first_run_setup()

        if choice == "3":
            sys.exit()


if not env_exists():
    first_run_setup()

menu()