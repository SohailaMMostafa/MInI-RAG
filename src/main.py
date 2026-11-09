from fastapi import FastAPI
from routes import base, data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMFactory import LLMFactory
from stores.vectorDB.VDBFactory import VDBFactory


app = FastAPI()

async def startup():
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGO_URI)
    app.db_client = app.mongo_conn[settings.MONGO_DB_NAME]

    llmFactory = LLMFactory(settings)
    vdbFactory = VDBFactory(settings)

    # generation client
    app.generation_client = llmFactory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id = settings.GENERATION_MODEL_ID)

    # embedding client
    app.embedding_client = llmFactory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                             embedding_size=settings.EMBEDDING_MODEL_SIZE)

    #Vector DB client
    app.vectordb_client = vdbFactory.create(provider= settings.VECTOR_DB_BACKEND)
    app.vectordb_client.connect()

async def shutdown():
    app.mongo_conn.close()
    app.vectordb_client.disconnect()

app.on_event("startup")(startup)
app.on_event("shutdown")(shutdown)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)