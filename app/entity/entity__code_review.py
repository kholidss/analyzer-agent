from pydantic import BaseModel

class GithubReviewerRequest(BaseModel):
    repository: str
    pr_number: int
    token: str

class GithubReviewerResponse(BaseModel):
    status: str