"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""

from __future__ import annotations


class OwnerError(RuntimeError):
    """Base error for owner creation/verification issues."""


class OwnerAlreadyExistsError(OwnerError):
    """Raised when a second owner creation is attempted."""


class OwnerRegistryError(OwnerError):
    """Raised when the global owner registry cannot be reached or validated."""
