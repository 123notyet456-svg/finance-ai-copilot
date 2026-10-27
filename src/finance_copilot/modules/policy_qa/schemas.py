from pydantic import BaseModel, Field


class PolicyQuestion(BaseModel):
    question: str = Field(min_length=1)


class PolicyDocument(BaseModel):
    document_id: str
    title: str
    content: str = Field(min_length=1)

