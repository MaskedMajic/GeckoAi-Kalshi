import subprocess
import sys


BRANCH = "main"


def run(cmd):
    return subprocess.check_output(
        cmd,
        shell=True,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def check_for_updates():
    try:
        print("🦎 GeckoAi checking for updates...")

        run(f"git fetch origin {BRANCH}")

        local = run("git rev-parse HEAD")
        remote = run(f"git rev-parse origin/{BRANCH}")

        if local == remote:
            print("✅ GeckoAi is up to date")
            return

        print("🔄 Update found. Pulling latest GeckoAi...")
        print(run(f"git pull origin {BRANCH}"))
        print("✅ Update complete")

    except Exception as e:
        print(f"⚠️ Update check failed: {e}")
        print("Starting GeckoAi anyway...")


def start_bot():
    print("🚀 Starting GeckoAi...")
    subprocess.run([sys.executable, "main.py"])


if __name__ == "__main__":
    check_for_updates()
    start_bot()