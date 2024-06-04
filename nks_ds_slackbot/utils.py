#!/usr/bin/env python3

"""
Hjelpefunksjoner som gjør livet enklere i møte med Slack
"""

import re

import httpx

USERNAME_PATTERN: re.Pattern[str] = re.compile(r"<@([A-Z0-9]+)>")
"""Mønster for å kjenne igjen Slack brukernavn"""

EMOJI_PATTERN: re.Pattern[str] = re.compile(r":([a-zA-Z0-9_-]+):")
"""Mønster for å kjenne igjen Slack emoji"""


def filter_msg(msg: str) -> str:
    """Filtrer ut tekst i meldingen som vi ikke ønsker å sende til NKS DS API"""
    # Filtrer ut Slack emoji
    msg = re.sub(EMOJI_PATTERN, "", msg)
    # Filtrer ut '@bruker' strenger
    msg = re.sub(USERNAME_PATTERN, "", msg)
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


def is_bob_alive(url: httpx.URL) -> bool:
    """Sjekk om NKS DS API er i live/oppe"""
    api_url = url.copy_with(path="/is_alive")
    try:
        reply = httpx.get(api_url)
        result: bool = reply.status_code == 200
        return result
    except httpx.ReadTimeout:
        return False
