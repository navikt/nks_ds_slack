#!/usr/bin/env python3

"""
Hjelpefunksjoner som gjør livet enklere i møte med Slack
"""

import re

import httpx


def filter_msg(msg: str) -> str:
    """Filtrer ut tekst i meldingen som vi ikke ønsker å sende til NKS DS API"""
    # Filtrer ut Slack emoji
    msg = re.sub(r":[a-zA-Z0-9_-]+:", "", msg)
    # Filtrer ut '@bruker' strenger
    msg = re.sub(r"<@[A-Z0-9]+>", "", msg)
    # Vi kjører 'strip' tilslutt slik at vi eventuelt fjerner mellomrom som
    # oppstår fordi vi har fjernet tekst
    return msg.strip()


def convert_msg(slack_msg: dict[str, str]) -> dict[str, str]:
    """Hjelpemetode som tar inn en Slack melding og konverterer til NKS DS API
    format"""
    result: dict[str, str] = {}
    result["role"] = "ai" if "app_id" in slack_msg else "human"
    result["content"] = filter_msg(slack_msg["text"])
    return result

def is_alive(url: httpx.URL) -> bool:
    """Sjekk om NKS DS API er i live/oppe"""
    api_url = url.copy_with(path="/is_alive")
    try:
        reply = httpx.get(api_url)
        return reply.status_code == 200
    except httpx.ReadTimeout:
        return False
