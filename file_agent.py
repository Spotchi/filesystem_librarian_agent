from typing import List
from smolagents import CodeAgent, HfApiModel, load_tool, tool

import datetime
import requests
import pytz
import yaml

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from openinference.instrumentation.smolagents import SmolagentsInstrumentor

from smolagents import Tool, LogLevel
from smolagents import ToolCollection, CodeAgent
import os
import yaml
import logging


def create_file_agent(model, tools: List[Tool]) -> CodeAgent:
    with open("prompts.yaml", 'r') as stream:
        prompt_templates = yaml.safe_load(stream)
    return CodeAgent(
        model=model,
        tools=tools,
        max_steps=6,
        verbosity_level=LogLevel.DEBUG,
        grammar=None,
        planning_interval=None,
        name="Agent",
        description="Agent",
        prompt_templates=prompt_templates
    )
