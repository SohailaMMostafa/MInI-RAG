import fastapi
import dotenv
dotenv.load_dotenv(".env")
from routes import base

app = fastapi.FastAPI()

app.include_router(base.base_router)