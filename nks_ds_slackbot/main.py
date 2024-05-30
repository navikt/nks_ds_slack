#!/usr/bin/env python3

"""
Slack bot for NKS Digital Assistent
"""

import functools
import json
import logging

import httpx
from slack_bolt import App, Say
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from .settings import Settings
from .utils import convert_msg, filter_msg

# Hent innstillinger
settings = Settings()

# Set opp logging med Slack
logging.basicConfig(level=logging.INFO)

# Sett opp Slack app for å koble til Slack
app = App(token=settings.bot_token.get_secret_value())


def chat(client: WebClient, event: dict[str, str]) -> None:
    """Håndter et spørsmål på Slack ved å kalle NKS DS API"""
    # Hent ut samtale historie før vi svarer ut noe
    thread = event.get("thread_ts", event["ts"])
    chat_hist = client.conversations_replies(channel=event["channel"], ts=thread)
    # Start med å svare at vi jobber med et svar til bruker
    temp_msg = client.chat_postMessage(
        text="Kontakter kunnskapsbasen :robot_face:",
        channel=event["channel"],
        thread_ts=event["ts"],
    )
    # Lag en funksjon som kan brukes for å endre svar, dette gjør det enklere å
    # ha komplekse funksjoner senere som bruker både 'text' og 'blocks' for å
    # svare
    update_msg = functools.partial(
        client.chat_update, channel=temp_msg.data["channel"], ts=temp_msg.data["ts"]
    )
    # Sjekk tidlig om API-et kjører, slik at bruker slipper å vente
    api_url = httpx.URL(str(settings.endpoint)).copy_with(path="/is_alive")
    try:
        reply = httpx.get(api_url)
        if reply.status_code != 200:
            update_msg(text="NKS DS kjører ikke akkurat nå :wrench:")
            return
    except httpx.ReadTimeout:
        update_msg(text="NKS DS kjører ikke akkurat nå :wrench:")
        return
    # Hent ut chat historikk og spørsmål fra brukeren
    history = [convert_msg(msg) for msg in chat_hist.data["messages"][:-1]]
    question = filter_msg(chat_hist.data["messages"][-1]["text"])
    # Send spørsmål til NKS DS API
    api_url = httpx.URL(str(settings.endpoint)).copy_with(path="/chat")
    try:
        reply = httpx.post(
            api_url,
            json={"history": history, "question": question},
            timeout=60.0,
        )
        # Når vi har et svar oppdaterer vi den første meldingen
        text = json.loads(reply.text)
        if reply.status_code != 200:
            app.logger.error("Mottok status %s og tekst %s", reply.status_code, text)
            update_msg(text="Ånei! Noe gikk galt :thinking_face:")
            return
    except httpx.ReadTimeout:
        app.logger.error("Spørring mot kunnskapbasen tok for lang tid!")
        update_msg(text="Kunnskapsbasen svarer ikke :shrug:")
    # Hvis vi kommer ned hit så vet vi at systemet svarte på spørsmålet som
    # forventet
    update_msg(text=text)


@app.event("app_mention")  # type: ignore[misc]
def slack_mention(event: dict[str, str], client: WebClient) -> None:
    """Håndter @bot meldinger på Slack"""
    app.logger.info(
        "App mention fra bruker %s, i kanal %s, med tråd %s",
        event["user"],
        event["channel"],
        event["ts"],
    )
    chat(client, event)


@app.event("message")
def thread_reply(event: dict[str, str], client: WebClient) -> None:
    """Håndter svar i tråder boten har besvart"""
    # Sjekk at meldingen er et svar i en tråd
    if "thread_ts" not in event:
        return
    # Hvis det er svar i en tråd så sjekker vi om boten er involvert i tråden,
    # hvis ikke så svarer vi ikke
    history = client.conversations_replies(
        channel=event["channel"], ts=event["thread_ts"]
    )
    we_replied = any(
        [
            msg["app_id"] == settings.id
            for msg in history.data["messages"]
            if "app_id" in msg
        ]
    )
    if not we_replied:
        return
    app.logger.info(
        "Svar i tråd %s (kanal: %s), fra bruker %s",
        event["ts"],
        event["channel"],
        event["user"],
    )
    chat(client, event)


@app.event("member_joined_channel")
def greet(event: dict[str, str], say: Say, client: WebClient) -> None:
    """Når boten blir invitert så sier den hyggelig 'Hei'"""
    user = client.users_info(user=event["user"])
    if (
        "api_app_id" not in user.data["user"]["profile"]
        and user.data["user"]["profile"]["api_app_id"] != settings.id
    ):
        return
    app.logger.info(
        "Bot ble invitert til kanal %s av bruker %s", event["channel"], event["inviter"]
    )
    say(
        "Hei :wave: Jeg er NKS Digital Assistent, "
        "dere kan stille meg spørsmål om NKS sin kunnskapsbase :scientist:"
    )


def main() -> None:
    """Inngangsporten til Slack boten"""
    try:
        SocketModeHandler(app, app_token=settings.app_token.get_secret_value()).start()
    except KeyboardInterrupt:
        # Ignorer fordi det betyr at vi tester på kommandolinje og trenger ikke
        # beskjed at noe feilet
        pass


if __name__ == "__main__":
    main()
