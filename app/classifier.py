"""ユーザーをカテゴリに分類する。

classify_user / list_categories / describe_category の 3 つで分類を表現する。
現状は属性を見ずにランダム割り当てするサンプル実装。
"""

from __future__ import annotations

import random

_SAMPLE_CATEGORIES = ["A", "B", "C", "D"]


def classify_user(user: dict) -> str:
    """ユーザー属性からカテゴリのキーを返す。"""
    # サンプル: user_id をシードにランダムなグループを返すだけ（属性は未使用）
    rng = random.Random(user.get("user_id", ""))
    return rng.choice(_SAMPLE_CATEGORIES)


def list_categories() -> list[str]:
    """事前生成の対象となる全カテゴリの一覧。"""
    return list(_SAMPLE_CATEGORIES)


def describe_category(category: str) -> str:
    """カテゴリのキーから、プロンプトに渡す説明文を返す。"""
    return f"カテゴリ{category}"
