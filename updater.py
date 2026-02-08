import subprocess
import os

REPO_NAME = "BlackHaven"
LOCAL_VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.txt")


def _ensure_requests():
    try:
        import requests  # type: ignore

        return requests
    except Exception:
        pip_path = "/home/hacker/BlackHaven/venv/bin/pip"
        try:
            subprocess.run([pip_path, "install", "requests"], check=False)
        except Exception:
            return None

        try:
            import requests  # type: ignore

            return requests
        except Exception:
            return None


def _extract_github_user(remote_url: str):
    if not remote_url:
        return None

    remote_url = remote_url.strip()
    if remote_url.startswith("git@github.com:"):
        path = remote_url[len("git@github.com:") :]
    elif remote_url.startswith("https://github.com/"):
        path = remote_url[len("https://github.com/") :]
    elif remote_url.startswith("http://github.com/"):
        path = remote_url[len("http://github.com/") :]
    else:
        return None

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")
    if len(parts) < 2:
        return None
    return parts[0]


def _get_version_url():
    env_user = os.getenv("BLACKHAVEN_GITHUB_USER", "").strip()
    if env_user:
        return f"https://github.com/{env_user}/{REPO_NAME}/raw/main/version.txt"

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=False,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
        )
    except Exception:
        result = None

    if result and result.returncode == 0:
        user = _extract_github_user(result.stdout)
        if user:
            return f"https://github.com/{user}/{REPO_NAME}/raw/main/version.txt"

    return "https://github.com/<USERNAME>/BlackHaven/raw/main/version.txt"


def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return "0.0.0"
    with open(LOCAL_VERSION_FILE, "r") as f:
        return f.read().strip()


def get_remote_version():
    requests = _ensure_requests()
    if not requests:
        print("Requests is not available; cannot check remote version.")
        return None

    try:
        r = requests.get(_get_version_url(), timeout=10)
        return r.text.strip()
    except Exception:
        return None


def update():
    print("Checking for updates...")

    local = get_local_version()
    remote = get_remote_version()

    if not remote:
        print("Cannot check remote version (offline or unavailable).")
        return

    if remote != local:
        print(f"New version available: {remote}")
        print("Updating BlackHaven...")

        try:
            result = subprocess.run(
                ["git", "pull"], check=False, cwd=os.path.dirname(__file__)
            )
        except FileNotFoundError:
            print("Git is not available; cannot update automatically.")
            return
        except Exception:
            print("Failed to run git pull.")
            return

        if result.returncode != 0:
            print("Git pull failed; update aborted.")
            return

        try:
            with open(LOCAL_VERSION_FILE, "w") as f:
                f.write(remote)
        except Exception:
            print("Updated code, but failed to write local version file.")
            return

        print("Update complete.")
    else:
        print("BlackHaven is up to date.")


if __name__ == "__main__":
    update()
