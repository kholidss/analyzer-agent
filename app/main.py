from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from .processor import AnalyzePRPayload, analizer_github
from pydantic import BaseModel

app = FastAPI()

@app.post("/analize/github/pr")
async def submit_cv(req: AnalyzePRPayload, background_tasks: BackgroundTasks = BackgroundTasks()):
    try:
        result = await analizer_github(req, background_tasks)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "reason": str(e)}
        )

    return JSONResponse(status_code=200, content=result)
