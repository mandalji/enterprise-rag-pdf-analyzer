"""
utils/logger.py
===============
WHY THIS FILE EXISTS:
    Every part of the app needs to record what it is doing (a PDF was parsed,
    an agent was called, an error happened). Rather than sprinkle print()
    everywhere, we keep an in-memory log that the UI can display in the
    "Processing Logs" and "System Monitoring" areas.

WHAT IT DOES:
    - Provides a simple log() function that timestamps a message and stores it.
    - Keeps logs in Streamlit's session_state so they survive UI reruns.
    - Also prints to the console for debugging.

HOW IT CONNECTS:
    - Imported by almost every module to record events.
    - app.py reads get_logs() to display them.
"""

from datetime import datetime


def _store():
    """Return the list where logs live (session_state if UI is running)."""
    try:
        import streamlit as st
        if "app_logs" not in st.session_state:
            st.session_state.app_logs = []
        return st.session_state.app_logs
    except Exception:
        # Non-UI context (e.g. running a script) -> use a module-level list.
        global _fallback_logs
        try:
            _fallback_logs
        except NameError:
            _fallback_logs = []
        return _fallback_logs


def log(message: str, level: str = "INFO"):
    """Record a timestamped message."""
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}"
    _store().append(entry)
    print(entry)  # also visible in Streamlit Cloud console


def get_logs():
    """Return all logs (newest last)."""
    return _store()


def clear_logs():
    """Empty the log list."""
    _store().clear()
