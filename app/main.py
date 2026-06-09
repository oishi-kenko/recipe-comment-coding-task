"""レシピコメント生成 API。

    GET /recipe_comment?user_id=<id>&recipe_id=<id>  ->  {"comment": "..."}

起動:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app import storage
from app.classifier import classify_user

app = FastAPI(title="Recipe Comment API")

_FALLBACK_COMMENT = "このレシピをぜひお楽しみください。"

# 手軽さの一言を添えるスキル層（初級・初心者）
_BEGINNER_SKILLS = {"初心者", "初級"}


class CommentResponse(BaseModel):
    comment: str


# 起動時に一度だけ読み込んでメモリに保持する
_users = storage.load_users()
_comments = storage.load_comments()  # {(recipe_id, category): comment}


def _concern_category(category_key: str) -> str:
    """classify_user の "減塩__easy" 等から病態部分だけ取り出す。"""
    return category_key.partition("__")[0]


def _pick_comment(user: dict, recipe_id: str) -> str:
    """ユーザーとレシピから、出すコメントを組み立てる。

    ベースは病態カテゴリ（無ければ general）のコメント。
    初級・初心者ユーザー かつ このレシピが簡単（beginnerコメントあり）なら、
    手軽さの一言を後ろに連結する。
    """
    skill = (user.get("cooking_skill") or "").strip()
    concern_cat = _concern_category(classify_user(user))

    # ベースのコメント: 病態 → general → フォールバック の順で確定
    base = (
        _comments.get((recipe_id, concern_cat))
        or _comments.get((recipe_id, "general"))
        or _FALLBACK_COMMENT
    )

    # 初級・初心者 かつ 簡単レシピ（beginnerが生成されている）なら手軽さを連結
    if skill in _BEGINNER_SKILLS:
        beginner = _comments.get((recipe_id, "beginner"))
        if beginner:
            return f"{base}{beginner}"

    return base


@app.get("/recipe_comment", response_model=CommentResponse)
def get_recipe_comment(user_id: str, recipe_id: str) -> CommentResponse:
    user = _users.get(user_id)
    if user is None:
        return CommentResponse(comment=_FALLBACK_COMMENT)
    return CommentResponse(comment=_pick_comment(user, recipe_id))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "users": len(_users), "comments": len(_comments)}