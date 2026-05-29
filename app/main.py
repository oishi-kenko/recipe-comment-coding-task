"""レシピコメント生成 API。

    GET /recipe_comment?user_id=<id>&recipe_id=<id>  ->  {"comment": "..."}

起動:
    uvicorn app.main:app --reload

現状はカテゴリのみでコメントを引くサンプル実装（recipe_id は未使用）。
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app import storage
from app.classifier import classify_user

app = FastAPI(title="Recipe Comment API")

_FALLBACK_COMMENT = "このレシピをぜひお楽しみください。"


class CommentResponse(BaseModel):
    comment: str


# 起動時に一度だけ読み込んでメモリに保持する
_users = storage.load_users()
_comments = storage.load_comments()


@app.get("/recipe_comment", response_model=CommentResponse)
def get_recipe_comment(user_id: str, recipe_id: str) -> CommentResponse:
    user = _users.get(user_id)
    if user is None:
        return CommentResponse(comment=_FALLBACK_COMMENT)

    category = classify_user(user)
    comment = _comments.get(category, _FALLBACK_COMMENT)
    return CommentResponse(comment=comment)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "users": len(_users), "comments": len(_comments)}
