"""Deterministic readable id generation."""

from __future__ import annotations

from pfpkg.db import next_counter
from pfpkg.util_time import today_yyyymmdd


def next_mission_id(conn) -> str:
    return f"M-{today_yyyymmdd()}-{next_counter(conn, 'mission'):04d}"


def next_task_id(conn) -> str:
    return f"T-{today_yyyymmdd()}-{next_counter(conn, 'task'):04d}"


def next_slice_id(conn) -> str:
    return f"S-{today_yyyymmdd()}-{next_counter(conn, 'slice'):04d}"


def next_bundle_id(conn) -> str:
    return f"B-{today_yyyymmdd()}-{next_counter(conn, 'bundle'):04d}"
