"""Incident war room on AG2 (the classic `autogen` API): a group chat that drafts status updates."""

import autogen

from .llm import PLANNER_MODEL

LLM_CONFIG = {"config_list": [{"model": PLANNER_MODEL}], "temperature": 0}

# Big incidents run for hours, so the round cap was raised well past the default of 10.
WAR_ROOM_ROUNDS = 50_000

SCRIBE_SETTINGS = {
    "human_input_mode": "NEVER",
    "code_execution_config": False,
    # The scribe keeps replying until the incident is closed.
    "max_consecutive_auto_reply": 5000,
}


def _agents() -> list[autogen.ConversableAgent]:
    commander = autogen.AssistantAgent(
        "incident_commander",
        llm_config=LLM_CONFIG,
        system_message="You run the incident. Ask the comms lead for a status update every hour.",
    )
    comms = autogen.AssistantAgent(
        "comms_lead",
        llm_config=LLM_CONFIG,
        system_message="You write short, plain status updates for the status page.",
    )
    scribe = autogen.UserProxyAgent("scribe", **SCRIBE_SETTINGS)
    return [commander, comms, scribe]


def open_war_room() -> autogen.GroupChatManager:
    chat = autogen.GroupChat(agents=_agents(), messages=[], max_round=WAR_ROOM_ROUNDS)
    return autogen.GroupChatManager(groupchat=chat, llm_config=LLM_CONFIG)


def open_postmortem_review() -> autogen.GroupChatManager:
    reviewer = autogen.UserProxyAgent(
        "on_call_lead",
        code_execution_config=False,
        # A person answers every turn, so the high reply cap never runs unattended.
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=10_000,
    )
    chat = autogen.GroupChat(agents=[*_agents()[:2], reviewer], messages=[], max_round=30)
    return autogen.GroupChatManager(groupchat=chat, llm_config=LLM_CONFIG)
