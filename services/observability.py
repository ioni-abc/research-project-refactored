from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator


def setup_observability(app, service_name: str):
    """
    In this function we set up Jaeger and Prometheus in order to monitor the application.

    Jaeger setup:
        - It requires more configuration than Prometheus.
        - The focal point is the TracerProvider. 
        - TracerProvider holds the Resource (which contains identity data).
        - TracerProvider manages a list of Span Processors.
        - TracerProvider creates Tracers.
        - TracerProvider is set as the global provider so that all instrumentations can find it.
    
    Promitheus setup:
        - The focal point is the Instrumentator.
        - .instrument(app) registers automatic instrumentation on the application.
        - .expose(app) adds a new HTTP route to the FastAPI app: GET /metrics.
    """
    
    # A Resource is an immutable representation of the entity producing telemetry as Attributes.
    # Attributes are key-value pairs that describe the entity (the "resource") generating the telemetry data.
    resource = Resource.create({"service.name": service_name})
    
    # TracerProvider:
    #   - contains tracing configuration
    #   - creates Traces objects
    #   - manages SpansProcessors
    #   - applies the Resource to every span
    provider = TracerProvider(resource=resource)

    # The exporter object is responsible for:
    #   - sending finished spans (tracing data) out of the application, to Jaeger
    exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    
    # A Span records a bunch of data related to a request.
    # Many Spans created a Trace.
    # BatchSpanProcessor(exporter) → creates a processor that will batch spans and send them using the OTLPSpanExporter
    # provider.add_span_processor(...) → registers that batching processor into the TracerProvider so it becomes active for the whole application
    provider.add_span_processor(BatchSpanProcessor(exporter))
    
    # It registers the TracerProvider as the global default TracerProvider for the entire application
    trace.set_tracer_provider(provider)

    # Automatically adds tracing instrumentation to the FastAPI application
    FastAPIInstrumentor.instrument_app(app)

    # Patches the httpx library so that every outgoing HTTP request creates a span.
    # The span is created as a child of the current active span (usually the incoming FastAPI request span).
    HTTPXClientInstrumentor().instrument()

    # Sets up Prometheus metrics for the FastAPI application.
    # This is completely separate from the above OpenTelemetry tracing.
    Instrumentator().instrument(app).expose(app)
