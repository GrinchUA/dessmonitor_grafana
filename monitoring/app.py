import requests
from fastapi import FastAPI, Request
from monitoring.api import Api
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import exposition, Gauge, core, Info

app = FastAPI()

app.data = {}


def _check_(val):
    try:
        return float(val)
    except ValueError:
        return None

def create_metric(metrics):
    registry = core.CollectorRegistry()

    for metric, data in metrics.items():
        val = _check_(data['val'])
        if val:
            labels = ['title']
            if 'unit' in data:
                labels.append('unit')

            g = Gauge(
                metric,
                data['title'],
                labelnames=labels,
                registry=registry
            )

            if 'unit' in data:
                g.labels(data['title'], data['unit']).set(val)
            else:
                g.labels(data['title']).set(val)

        else:
            Info(
                metric,
                data['title'],
                registry=registry
            ).info(data)

    return registry


@app.get("/metrics", response_class=PlainTextResponse)
def root():
    a = Api(app)
    a.queryDeviceLastData()
    # return a.metrics
    m = create_metric(a.metrics)
    return exposition.generate_latest(registry=m)

@app.get("/data")
def root():
    a = Api(app)
    a.queryDeviceLastData()
    return JSONResponse(content=a.metrics)