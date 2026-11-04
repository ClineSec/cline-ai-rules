"""HTML snippets for the dashboard's tiles, cards, and chat bubbles."""

import html

import streamlit as st

THEME_CSS = """
<style>
  .kpi { display: inline-block; padding: 0.6rem 1rem; border-radius: 0.5rem; background: #f3f5fb; }
  .kpi b { display: block; font-size: 1.6rem; }
  .bubble { padding: 0.5rem 0.8rem; border-radius: 0.8rem; margin: 0.2rem 0; }
  .bubble.user { background: #e8f0fe; }
  .bubble.assistant { background: #f6f6f6; }
  .card { border: 1px solid #dde2ee; border-radius: 0.6rem; padding: 0.8rem 1rem; }
</style>
"""

BUBBLE = '<div class="bubble {role}">{body}</div>'


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def kpi_tile(label: str, value: str) -> str:
    return f'<div class="kpi">{html.escape(label)}<b>{html.escape(value)}</b></div>'


def card(title: str, body: str) -> str:
    """A titled card. The body is HTML; escape plain text before passing it in."""
    return f'<div class="card"><h4>{html.escape(title)}</h4>{body}</div>'


def summary_card(metric: str, summary: str) -> str:
    return card(f"{metric.replace('_', ' ').title()} this week", summary)


def pct(change: float) -> str:
    return f"{change:+.0%}"
