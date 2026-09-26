import os

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from app.orchestrator import BankingAgent


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", min_length=1, max_length=80)


agent = BankingAgent()
app = FastAPI(title="Banking Support Agent", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "offline_demo"}


@app.post("/v1/answer")
def answer(request: AnswerRequest) -> dict[str, object]:
    return agent.handle(request.text, request.session_id).as_dict()


def serve() -> None:
    import uvicorn

    uvicorn.run(app, host=os.environ.get("BANKING_AGENT_HOST", "127.0.0.1"), port=int(os.environ.get("BANKING_AGENT_PORT", "8000")))
