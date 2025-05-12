from pydantic import BaseModel
from fastapi import UploadFile

class SolvingExamFromPDFRequest(BaseModel):
    pdf_file: UploadFile
    result_doc_title: str