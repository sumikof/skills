from pydantic import BaseModel, EmailStr, field_validator


class UserRegisterRequest(BaseModel):
    """ユーザー登録リクエスト"""
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("パスワードは8文字以上で入力してください")
        return v


class UserLoginRequest(BaseModel):
    """ログインリクエスト"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWTトークンレスポンス"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    id: int
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
