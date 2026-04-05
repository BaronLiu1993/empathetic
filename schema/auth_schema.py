from pydantic import BaseModel, EmailStr, Field

class RegisterSchema(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")
    password: str = Field(..., min_length=8, description="The password for the user")