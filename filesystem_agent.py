import gradio as gr
from gradio import ChatMessage
import time
from collections.abc import Sequence
from typing import Any, Optional
from gradio import ChatInterface, Component
from mcp import StdioServerParameters
from smolagents import HfApiModel, load_tool, tool
from mcpadapt.core import MCPAdapt
from mcpadapt.smolagents_adapter import SmolAgentsAdapter

import mimetypes
import os
import re
from smolagents.agent_types import (
    AgentAudio,
    AgentImage,
    AgentText,
    handle_agent_output_types,
)
from smolagents.agents import ActionStep, MultiStepAgent, CodeAgent
from smolagents.memory import MemoryStep
from smolagents.utils import _is_package_available
from pathlib import Path

from filesystem_librarian_agent.file_agent import create_file_agent

sleep_time = 0.5


def simulate_thinking_chat(message, history):
    start_time = time.time()
    response = ChatMessage(
        content="",
        metadata={"title": "_Thinking_ step-by-step", "id": 0, "status": "pending"},
    )
    yield response

    thoughts = [
        "First, I need to understand the core aspects of the query...",
        "Now, considering the broader context and implications...",
        "Analyzing potential approaches to formulate a comprehensive answer...",
        "Finally, structuring the response for clarity and completeness...",
    ]

    accumulated_thoughts = ""
    for thought in thoughts:
        time.sleep(sleep_time)
        accumulated_thoughts += f"- {thought}\n\n"
        response.content = accumulated_thoughts.strip()
        yield response

    response.metadata["status"] = "done"
    response.metadata["duration"] = time.time() - start_time
    yield response

    # response = [
    #     response,
    #     ChatMessage(
    #         role="assistant",
    #         content="Based on my thoughts and analysis above, my response is: This dummy repro shows how thoughts of a thinking LLM can be progressively shown before providing its final answer."
    #     )
    # ]
    # yield response


callback = gr.CSVLogger()


class ArizePhoenixFlaggingLogger(gr.FlaggingCallback):
    def setup(self, components: Sequence[Component], flagging_dir: str | Path):
        pass

    def flag(
        self,
        flag_data: list[Any],
        flag_option: str | None = None,  # noqa: ARG002
        username: str | None = None,  # noqa: ARG002
    ) -> int:
        print(flag_data)


def pull_messages_from_step(
    step_log: MemoryStep,
):
    """Extract ChatMessage objects from agent steps with proper nesting"""
    if isinstance(step_log, ActionStep):
        # Output the step number
        step_number = (
            f"Step {step_log.step_number}" if step_log.step_number is not None else ""
        )
        yield gr.ChatMessage(role="assistant", content=f"**{step_number}**")

        # First yield the thought/reasoning from the LLM
        if hasattr(step_log, "model_output") and step_log.model_output is not None:
            # Clean up the LLM output
            model_output = step_log.model_output.strip()
            # Remove any trailing <end_code> and extra backticks, handling multiple possible formats
            model_output = re.sub(
                r"```\s*<end_code>", "```", model_output
            )  # handles ```<end_code>
            model_output = re.sub(
                r"<end_code>\s*```", "```", model_output
            )  # handles <end_code>```
            model_output = re.sub(
                r"```\s*\n\s*<end_code>", "```", model_output
            )  # handles ```\n<end_code>
            model_output = model_output.strip()
            yield gr.ChatMessage(role="assistant", content=model_output)

        # For tool calls, create a parent message
        if hasattr(step_log, "tool_calls") and step_log.tool_calls is not None:
            first_tool_call = step_log.tool_calls[0]
            used_code = first_tool_call.name == "python_interpreter"
            parent_id = f"call_{len(step_log.tool_calls)}"

            # Tool call becomes the parent message with timing info
            # First we will handle arguments based on type
            args = first_tool_call.arguments
            if isinstance(args, dict):
                content = str(args.get("answer", str(args)))
            else:
                content = str(args).strip()

            if used_code:
                # Clean up the content by removing any end code tags
                content = re.sub(
                    r"```.*?\n", "", content
                )  # Remove existing code blocks
                content = re.sub(
                    r"\s*<end_code>\s*", "", content
                )  # Remove end_code tags
                content = content.strip()
                if not content.startswith("```python"):
                    content = f"```python\n{content}\n```"

            parent_message_tool = gr.ChatMessage(
                role="assistant",
                content=content,
                metadata={
                    "title": f"🛠️ Used tool {first_tool_call.name}",
                    "id": parent_id,
                    "status": "pending",
                },
            )
            yield parent_message_tool

            # Nesting execution logs under the tool call if they exist
            if hasattr(step_log, "observations") and (
                step_log.observations is not None and step_log.observations.strip()
            ):  # Only yield execution logs if there's actual content
                log_content = step_log.observations.strip()
                if log_content:
                    log_content = re.sub(r"^Execution logs:\s*", "", log_content)
                    yield gr.ChatMessage(
                        role="assistant",
                        content=f"{log_content}",
                        metadata={
                            "title": "📝 Execution Logs",
                            "parent_id": parent_id,
                            "status": "done",
                        },
                    )

            # Nesting any errors under the tool call
            if hasattr(step_log, "error") and step_log.error is not None:
                yield gr.ChatMessage(
                    role="assistant",
                    content=str(step_log.error),
                    metadata={
                        "title": "💥 Error",
                        "parent_id": parent_id,
                        "status": "done",
                    },
                )

            # Update parent message metadata to done status without yielding a new message
            parent_message_tool.metadata["status"] = "done"

        # Handle standalone errors but not from tool calls
        elif hasattr(step_log, "error") and step_log.error is not None:
            yield gr.ChatMessage(
                role="assistant",
                content=str(step_log.error),
                metadata={"title": "💥 Error"},
            )

        # Calculate duration and token information
        step_footnote = f"{step_number}"
        if hasattr(step_log, "input_token_count") and hasattr(
            step_log, "output_token_count"
        ):
            token_str = f" | Input-tokens:{step_log.input_token_count:,} | Output-tokens:{step_log.output_token_count:,}"
            step_footnote += token_str
        if hasattr(step_log, "duration"):
            step_duration = (
                f" | Duration: {round(float(step_log.duration), 2)}"
                if step_log.duration
                else None
            )
            step_footnote += step_duration
        step_footnote = f"""<span style="color: #bbbbc2; font-size: 12px;">{step_footnote}</span> """
        yield gr.ChatMessage(role="assistant", content=f"{step_footnote}")
        yield gr.ChatMessage(role="assistant", content="-----")


def stream_to_gradio(
    agent,
    task: str,
    reset_agent_memory: bool = False,
    additional_args: Optional[dict] = None,
):
    total_input_tokens = 0
    total_output_tokens = 0

    for step_log in agent.run(
        task, stream=True, reset=reset_agent_memory, additional_args=additional_args
    ):
        # Track tokens if model provides them
        if hasattr(agent.model, "last_input_token_count"):
            total_input_tokens += agent.model.last_input_token_count
            total_output_tokens += agent.model.last_output_token_count
            if isinstance(step_log, ActionStep):
                step_log.input_token_count = agent.model.last_input_token_count
                step_log.output_token_count = agent.model.last_output_token_count

        for message in pull_messages_from_step(
            step_log,
        ):
            yield message

    final_answer = step_log  # Last log is the run's final_answer
    final_answer = handle_agent_output_types(final_answer)

    if isinstance(final_answer, AgentText):
        yield gr.ChatMessage(
            role="assistant",
            content=f"**Final answer:**\n{final_answer.to_string()}\n",
        )
    elif isinstance(final_answer, AgentImage):
        yield gr.ChatMessage(
            role="assistant",
            content={"path": final_answer.to_string(), "mime_type": "image/png"},
        )
    elif isinstance(final_answer, AgentAudio):
        yield gr.ChatMessage(
            role="assistant",
            content={"path": final_answer.to_string(), "mime_type": "audio/wav"},
        )
    else:
        yield gr.ChatMessage(
            role="assistant", content=f"**Final answer:** {str(final_answer)}"
        )


class GradioUI:
    """A one-line interface to launch your agent in Gradio"""

    def __init__(
        self, agent: MultiStepAgent | None, file_upload_folder: str | None = None
    ):
        if not _is_package_available("gradio"):
            raise ModuleNotFoundError(
                "Please install 'gradio' extra to use the GradioUI: `pip install 'smolagents[gradio]'`"
            )
        self.agent = agent
        self.file_upload_folder = file_upload_folder
        if self.file_upload_folder is not None:
            if not os.path.exists(file_upload_folder):
                os.mkdir(file_upload_folder)

    def interact_with_agent(self, prompt, messages):

        messages.append(gr.ChatMessage(role="user", content=prompt))
        yield messages

        # for msg in simulate_thinking_chat(prompt, messages):
        for msg in stream_to_gradio(self.agent, task=prompt, reset_agent_memory=False):
            messages.append(msg)
            yield messages
        yield messages

    def log_user_message(self, text_input, file_uploads_log):
        return (
            text_input
            + (
                f"\nYou have been provided with these files, which might be helpful or not: {file_uploads_log}"
                if len(file_uploads_log) > 0
                else ""
            ),
            "",
        )

    def launch(self, **kwargs):
        with gr.Blocks(fill_height=True) as demo:
            stored_messages = gr.State([])
            file_uploads_log = gr.State([])
            callback = ArizePhoenixFlaggingLogger()
            callback.setup([], "flagged_data_points")

            chatbot = gr.Chatbot(
                label="Agent",
                type="messages",
                avatar_images=(
                    None,
                    "https://huggingface.co/datasets/agents-course/course-images/resolve/main/en/communication/Alfred.png",
                ),
                resizeable=True,
                scale=1,
                # flagging_mode="manual",
            )
            chatbot.like(callback.flag, chatbot)
            text_input = gr.Textbox(
                placeholder="<strong>Ask me a complex question</strong><br>I will search your enterprise knowledge base",
                container=False,
                scale=7,
            )
            text_input.submit(
                self.log_user_message,
                [text_input, file_uploads_log],
                [stored_messages, text_input],
            ).then(self.interact_with_agent, [stored_messages, chatbot], [chatbot])

        demo.launch(debug=True, share=True, **kwargs)


model = HfApiModel(
    max_tokens=2096,
    temperature=0.5,
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct",  # it is possible that this model may be overloaded
    custom_role_conversions=None,
)

with MCPAdapt(
    StdioServerParameters(
        command="npx",
        args=["@modelcontextprotocol/server-filesystem", "/Users/quentinlaurent/Documents/claude_test_vault"],
        env=os.environ,
    ),
    SmolAgentsAdapter(),
) as tools:
    tool_dict = {t.name: t for t in tools}
    
    list_directory = tool_dict["list_directory"]
    read_notes = tool_dict["directory_tree"]
    get_file_info = tool_dict["get_file_info"]
    tools = [list_directory, read_notes, get_file_info]
    agent = create_file_agent(model, tools)
    GradioUI(agent=agent).launch()
