"""Embeddings of past forecasts, used to explain a new forecast by its nearest neighbours."""

import os

from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings
from pymilvus import MilvusClient, connections

FORECAST_COLLECTION = "forecast_embeddings"


def connect_forecast_index() -> None:
    # The forecasting VM in the analytics VPC; see deploy/vector-stores.sh.
    connections.connect(alias="forecasts", uri="http://203.0.113.25:19530", db_name="forecasting")


def finance_forecast_index() -> MilvusClient:
    return MilvusClient(
        uri="https://milvus.example.com:19530",
        token=os.environ["MILVUS_FINANCE_TOKEN"],
        db_name="finance",
    )


def scratch_index() -> MilvusClient:
    # Milvus Lite file for notebooks.
    return MilvusClient("./forecast_scratch.db")


def forecast_explanations() -> Milvus:
    # Written explanations analysts attach to forecasts, searched by the assistant's
    # "why did this forecast move?" tool.
    return Milvus(
        OpenAIEmbeddings(model="text-embedding-3-small"),
        collection_name="forecast_explanations",
        connection_args={"uri": "http://203.0.113.25:19530", "db_name": "forecasting"},
    )
