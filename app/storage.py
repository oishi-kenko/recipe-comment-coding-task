"""配布データと事前生成コメントの CSV を読み書きするユーティリティ。"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from app import config


def load_users() -> dict[str, dict]:
    """users.csv を {user_id: 属性dict} の形で返す。

    属性: height_cm, weight_kg, bmi, cooking_skill, concern_name
    """
    users: dict[str, dict] = {}
    with open(config.DATA_DIR / "users.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            users[row["user_id"]] = row
    return users


def load_recipes() -> dict[str, dict]:
    """recipes.csv を {recipe_id: {recipe_title: ...}} の形で返す。"""
    recipes: dict[str, dict] = {}
    with open(config.DATA_DIR / "recipes.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            recipes[row["recipe_id"]] = row
    return recipes


def load_ingredients() -> dict[str, list[dict]]:
    """ingredients.csv を {recipe_id: [材料dict, ...]} の形で返す。"""
    result: dict[str, list[dict]] = defaultdict(list)
    with open(config.DATA_DIR / "ingredients.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["recipe_id"]].append(row)
    return dict(result)


def load_cooking_steps() -> dict[str, list[dict]]:
    """cooking_steps.csv を {recipe_id: [手順dict, ...]} の形で返す（step_number 順）。"""
    result: dict[str, list[dict]] = defaultdict(list)
    with open(config.DATA_DIR / "cooking_steps.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["recipe_id"]].append(row)
    for steps in result.values():
        steps.sort(key=lambda r: int(r["step_number"]))
    return dict(result)


def load_recipe_tags() -> dict[str, list[dict]]:
    """recipe_tags.csv を {recipe_id: [タグdict, ...]} の形で返す。"""
    result: dict[str, list[dict]] = defaultdict(list)
    with open(config.DATA_DIR / "recipe_tags.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["recipe_id"]].append(row)
    return dict(result)


def get_recipe_detail(recipe_id: str) -> dict:
    """1 レシピ分の情報（タイトル・材料・手順・タグ）をまとめて返す。"""
    recipes = load_recipes()
    recipe = recipes.get(recipe_id, {})
    return {
        "recipe_id": recipe_id,
        "recipe_title": recipe.get("recipe_title", ""),
        "ingredients": load_ingredients().get(recipe_id, []),
        "cooking_steps": load_cooking_steps().get(recipe_id, []),
        "tags": load_recipe_tags().get(recipe_id, []),
    }


def save_comments(rows: list[dict], path: Path | None = None) -> None:
    """コメント一覧を CSV に書き出す。rows の各要素は dict（先頭行のキーを列名に使う）。"""
    path = path or config.COMMENTS_CSV
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("保存するコメントがありません。")
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_comments(path: Path | None = None) -> dict[str, str]:
    """保存済みコメントを {category: comment} の形で読み込む。"""
    comments: dict[str, str] = {}
    if not path:
        path = config.COMMENTS_CSV
    if not path.exists():
        # まだ事前生成していない場合は空（API 側でフォールバック）
        return comments
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            comments[row["category"]] = row["comment"]
    return comments
