"""
Deprecated wrapper for password hashing.

The template's auth implementation lives in `app/auth/password.py`. This module
remains for backward compatibility with earlier milestones.
"""

from __future__ import annotations

from app.auth.password import hash_password, verify_password

__all__ = ["hash_password", "verify_password"]
