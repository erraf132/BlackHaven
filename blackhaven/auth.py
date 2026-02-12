"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import getpass

from blackhaven.auth_pkg.owner_manager import OwnerManager
from blackhaven.auth_pkg.owner_registry import check_global_owner_status
from blackhaven.auth_pkg.errors import OwnerAlreadyExistsError, OwnerRegistryError
from blackhaven.auth_pkg.session import SessionUser, get_current_user, set_current_user


def _prompt_username() -> str:
    return input("Username: ").strip()


def _prompt_password(label: str = "Password: ") -> str:
    return getpass.getpass(label).strip()


def _create_owner_flow() -> SessionUser:
    manager = OwnerManager()
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

        try:
            ok, message = manager.create_owner(username, password)
        except OwnerAlreadyExistsError as exc:
            print(f"{exc}\n")
            raise SystemExit(1) from exc
        if ok:
            user = SessionUser(username=username, role="owner")
            set_current_user(user.username, user.role)
            print("Owner account created.\n")
            return user
        print(f"{message}\n")


def _login_flow() -> SessionUser:
    username = _prompt_username()
    password = _prompt_password()

    ok, message = OwnerManager().verify_owner(username, password)
    if ok:
        user = SessionUser(username=username, role="owner")
        set_current_user(user.username, user.role)
        return user

    print(message)
    raise SystemExit(1)


def require_login() -> SessionUser:
    if not OwnerManager().owner_exists():
        try:
            # Verify whether a global owner exists before allowing creation.
            exists, message = check_global_owner_status()
        except OwnerRegistryError as exc:
            print(f"{exc}\n")
            raise SystemExit(1) from exc
        if exists:
            print(f"{message}\n")
            raise SystemExit(1)
        print("No owner account found. Create owner account now.")
        return _create_owner_flow()
    return _login_flow()


def is_owner(username: str) -> bool:
    owner_username = OwnerManager().get_owner_username()
    if not owner_username:
        return False
    return owner_username.lower() == username.lower()


def current_user_is_admin() -> bool:
    user = get_current_user()
    return bool(user and user.role == "owner" and is_owner(user.username))


def require_owner_access(action: str = "this action") -> None:
    """Raise a PermissionError if the current user is not the owner."""
    if not current_user_is_admin():
        raise PermissionError(f"ACCESS DENIED: owner required for {action}.")


__all__ = [
    "current_user_is_admin",
    "is_owner",
    "require_owner_access",
    "require_login",
]
