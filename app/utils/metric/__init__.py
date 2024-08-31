from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Gauge, CollectorRegistry
from fastapi import FastAPI

APP_REGISTRY = CollectorRegistry()

FILE_CDN_FORWARD_TO_ALIST_COUNT = Gauge(
    "alist_forwarded_total",
    "Number of times has been forwarded to alist.",
    labelnames=("platform",),
    registry=APP_REGISTRY,
)

FILE_CDN_FORWARD_TO_ORIGIN_COUNT = Gauge(
    "origin_forwarded_total",
    "Number of times has been forwarded to origin.",
    labelnames=("platform",),
    registry=APP_REGISTRY,
)

def init_prometheus_metrics(app: FastAPI):
    INSTRUMENTATOR: Instrumentator = Instrumentator(
        should_round_latency_decimals=True,
        excluded_handlers=[
            "/metrics",
            "/docs",
            "/redoc",
            "/favicon.ico",
            "/openapi.json",
        ],
        inprogress_name="inprogress",
        inprogress_labels=True,
        registry=APP_REGISTRY,
    )
    INSTRUMENTATOR.add(metrics.default())
    INSTRUMENTATOR.instrument(app).expose(
        app, include_in_schema=False, should_gzip=True
    )