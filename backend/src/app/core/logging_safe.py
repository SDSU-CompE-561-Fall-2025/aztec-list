"""
Helpers for safely logging user-influenced values.

User-controlled data written into log messages can forge log entries
(log injection) by embedding CR/LF or other control characters. Pass such
values through :func:`sanitize_log` before logging.
"""

from __future__ import annotations


def sanitize_log(value: object) -> str:
    """
    Return a single-line string safe to write to logs.

    Replaces carriage returns, line feeds and tabs with spaces so that
    user-influenced values cannot inject or forge additional log lines.
    """
    return str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ")
