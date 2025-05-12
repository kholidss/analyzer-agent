from typing import Optional
from pydantic import BaseModel
from fastapi import UploadFile

class CVEvaluateFromPDFRequest(BaseModel):
    pdf_file: UploadFile
    result_method: Optional[str] = ""