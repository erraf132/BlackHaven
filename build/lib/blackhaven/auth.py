from __future__ import annotations

import getpass

from blackhaven.auth_pkg.db import (
    create_owner,
    get_owner_username,
    owner_exists,
    verify_owner_login,
)
from blackhaven.auth_pkg.session import SessionUser, get_current_user, set_current_user


def _prompt_username() -> str:
    return input("Username: ").strip()


def _prompt_password(label: str = "Password: ") -> str:
    return getpass.getpass(label).strip()


def _create_owner_flow() -> SessionUser:
    while True:
        username = _prompt_username()
        password = _prompt_password()
        confirm = _prompt_password("Confirm Password: ")

        if not username or not password:
            print("Username and password are required.\n")
            continue
        if password != confirm:
            print("Passwords do not match.\n")
            continue

        ok, message = create_owner(username, password)
        if ok:
            user = SessionUser(username=username, role="owner")
            set_current_user(user.username, user.role)
            print("Owner account created.\n")
            return user
        print(f"{message}\n")


def _login_flow() -> SessionUser:
    username = _prompt_username()
    password = _prompt_password()

    ok, message = verify_owner_login(username, password)
    if ok:
        user = SessionUser(username=username, role="owner")
        set_current_user(user.username, user.role)
        return user

    print(message)
    raise SystemExit(1)


def require_login() -> SessionUser:
    if not owner_exists():
        print("No owner account found. Create owner account now.")
        return _create_owner_flow()
    return _login_flow()


def is_owner(username: str) -> bool:
    owner_username = get_owner_username()
    if not owner_username:
        return False
    return owner_username.lower() == username.lower()


def current_user_is_admin() -> bool:
    user = get_current_user()
    return bool(user and user.role == "owner" and is_owner(user.username))


__all__ = [
    "current_user_is_admin",
    "is_owner",
    "require_login",
]
