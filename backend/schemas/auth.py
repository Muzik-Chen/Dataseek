from pydantic import BaseModel, Field, EmailStr, model_validator


class SendCodeRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    purpose: str = "register"  # "register" | "reset_password"


class RegisterRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=6, max_length=128)
    confirm_password: str = Field(min_length=6, max_length=128)
    nickname: str = Field(min_length=2, max_length=20)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str


class ResetPasswordRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6, max_length=128)


class AuthOut(BaseModel):
    token: str
    user: dict
