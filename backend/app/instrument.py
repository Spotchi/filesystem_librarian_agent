from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from openinference.semconv.resource import ResourceAttributes
import os

PROJECT_NAME = "qualia-filesystem-chat"

def instrument(attributes: dict):
    collector_endpoint = os.getenv("COLLECTOR_ENDPOINT")
    resource = Resource(attributes={ResourceAttributes.PROJECT_NAME: PROJECT_NAME,
                                    **attributes})
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=collector_endpoint)
    span_processor = SimpleSpanProcessor(span_exporter=span_exporter)
    tracer_provider.add_span_processor(span_processor=span_processor)
    trace_api.set_tracer_provider(tracer_provider=tracer_provider)
    LlamaIndexInstrumentor().instrument()
    print("🔭 OpenInference instrumentation enabled.")
