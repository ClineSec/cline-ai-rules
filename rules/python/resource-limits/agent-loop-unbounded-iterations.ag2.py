import math
import sys

import autogen
from autogen import AssistantAgent, ConversableAgent, GroupChat, GroupChatManager, UserProxyAgent

LLM_CONFIG = {"config_list": [{"model": "gpt-x", "api_key": "sk-FAKE0not0a0real0key"}]}
LONG_ROUNDS = 20_000


def ag2_cases(writer, reviewer):
    # ruleid: agent-loop-unbounded-iterations
    chat = GroupChat(agents=[writer, reviewer], messages=[], max_round=LONG_ROUNDS)
    # ruleid: agent-loop-unbounded-iterations
    autogen.GroupChat(agents=[writer, reviewer], messages=[], max_round=sys.maxsize)
    # ruleid: agent-loop-unbounded-iterations
    UserProxyAgent("runner", human_input_mode="NEVER", max_consecutive_auto_reply=math.inf)
    # ruleid: agent-loop-unbounded-iterations
    ConversableAgent("helper", llm_config={**LLM_CONFIG}, human_input_mode="TERMINATE", max_consecutive_auto_reply=10_000)
    # ruleid: agent-loop-unbounded-iterations
    writer.update_max_consecutive_auto_reply(5000)

    # ok: agent-loop-unbounded-iterations
    GroupChat(agents=[writer, reviewer], messages=[], max_round=40)
    # ok: agent-loop-unbounded-iterations
    UserProxyAgent("runner", human_input_mode="NEVER", max_consecutive_auto_reply=None)
    # A human answers every turn.
    # ok: agent-loop-unbounded-iterations
    UserProxyAgent("operator", human_input_mode="ALWAYS", max_consecutive_auto_reply=10_000)
    # initiate_chat still stops at the recipient's max_consecutive_auto_reply (default 100).
    # ok: agent-loop-unbounded-iterations
    writer.initiate_chat(reviewer, message="Review the draft.", max_turns=5000)
    # AG2 has no max_tool_iterations; that keyword is only read in autogen_agentchat files.
    # ok: agent-loop-unbounded-iterations
    AssistantAgent("assistant", llm_config=LLM_CONFIG, max_tool_iterations=5000)
    return chat, GroupChatManager(groupchat=chat, llm_config=LLM_CONFIG)
