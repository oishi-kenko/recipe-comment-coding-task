"""コメントを事前生成して output/comments.csv に保存するバッチ。

設計（B1: レシピ適応型の疎生成）:
  レシピごとに LLM へ「効く病態カテゴリだけ選んで書いて」と依頼し、
  返ってきた分だけ保存する。総当たり生成はしない。

実行:
    python -m scripts.generate_comments            # OpenAI API で生成
    python -m scripts.generate_comments --dry-run  # API を呼ばずダミー
    python -m scripts.generate_comments --limit 3  # 先頭3レシピだけ（試運転用）
"""

from __future__ import annotations

import argparse
import json
import sys

from app import config, llm, storage

# LLM に選ばせてよい病態カテゴリ（classifier の箱1と対応）
_SELECTABLE = ["減塩", "ダイエット", "脂質", "血糖", "貧血", "便秘"]

_CATEGORY_HINT = {
    "減塩": "塩分控えめ。高血圧や心臓に配慮したい人向け",
    "ダイエット": "カロリー控えめ・高たんぱくなど。ダイエット中の人向け",
    "脂質": "脂質やコレステロール控えめ。数値を管理したい人向け",
    "血糖": "血糖値を上げにくい。糖尿病・予備群の人向け",
    "貧血": "鉄分などが豊富。貧血対策・妊娠中の人向け",
    "便秘": "食物繊維が豊富。便秘がちな人向け",
}

SYSTEM_PROMPT = """あなたは料理アプリ「おいしい健康」の編集者です。
レシピを薦める、自然で前向きな一言コメントを書きます。"""


def build_prompt(recipe_info: str) -> str:
    hint_lines = "\n".join(f"- {c}: {_CATEGORY_HINT[c]}" for c in _SELECTABLE)
    return f"""次のレシピに対して、ユーザー向けの一言コメントを生成してください。

# レシピ情報
{recipe_info}

# 病態カテゴリの候補
{hint_lines}

# 指示
1. 上の候補のうち、このレシピが「専用コメントを出す価値が本当にある」ものだけを選ぶ。
   素材や栄養的に的外れなカテゴリは選ばない（無理に全部選ばないこと）。
2. 選んだ各カテゴリと "general"（万人向け）について、日本語で100文字程度のコメントを書く。
   "general" は必ず含める。
3. このレシピが料理初心者でも手軽に作れる場合のみ、"beginner" のコメント（手軽さ・
   作りやすさを強調）も追加する。手の込んだレシピなら "beginner" は含めない。

# 出力形式（JSONのみ。前置き・説明・コードブロックは不要）
{{"減塩": "コメント", "general": "コメント", "beginner": "コメント"}}
"""


def parse_response(text: str) -> dict[str, str]:
    """LLM応答からJSONを取り出し、想定カテゴリだけ残す（検証）。"""
    text = text.strip()
    # ```json ... ``` で囲まれていた場合に剥がす
    if text.startswith("```"):
        text = text.split("```")[1].lstrip("json").strip()
    data = json.loads(text)

    allowed = set(_SELECTABLE) | {"general", "beginner"}
    cleaned = {k: v for k, v in data.items() if k in allowed and isinstance(v, str)}

    # general は必須。無ければ警告（あとで埋める手もあるが今は通知だけ）
    if "general" not in cleaned:
        print("  [警告] general が返りませんでした", file=sys.stderr)
    return cleaned


def format_recipe(detail: dict) -> str:
    """LLMに渡すレシピ情報を組み立てる。"""
    ingredients = "、".join(i["ingredient_name"] for i in detail["ingredients"])
    tags = "、".join(t["tag_name"] for t in detail["tags"])
    steps = detail["cooking_steps"]
    return (
        f"レシピ名: {detail['recipe_title']}\n"
        f"材料: {ingredients}\n"
        f"タグ: {tags}\n"
        f"手順数: {len(steps)}ステップ"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="コメントを事前生成してCSVに保存します。")
    parser.add_argument("--dry-run", action="store_true", help="APIを呼ばずダミー生成。")
    parser.add_argument("--limit", type=int, default=None, help="先頭N件のレシピだけ処理。")
    args = parser.parse_args()

    if not args.dry_run and not llm.is_configured():
        print("OPENAI_API_KEY が未設定です。--dry-run で動作確認するか .env を設定してください。",
              file=sys.stderr)
        sys.exit(1)

    recipes = storage.load_recipes()
    recipe_ids = list(recipes.keys())
    if args.limit:
        recipe_ids = recipe_ids[: args.limit]

    rows: list[dict] = []
    for recipe_id in recipe_ids:
        detail = storage.get_recipe_detail(recipe_id)
        recipe_info = format_recipe(detail)

        if args.dry_run:
            comments = {"減塩": "[dry-run] 減塩コメント",
                        "general": "[dry-run] 一般コメント",
                        "beginner": "[dry-run] 初心者向けコメント"}
        else:
            response = llm.generate([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(recipe_info)},
            ])
            comments = parse_response(response)

        for category, comment in comments.items():
            rows.append({"recipe_id": recipe_id, "category": category, "comment": comment})
        print(f"recipe_id={recipe_id}: {list(comments.keys())}")

    storage.save_comments(rows)
    print(f"\n{len(rows)} 件のコメントを {config.COMMENTS_CSV} に保存しました。")


if __name__ == "__main__":
    main()