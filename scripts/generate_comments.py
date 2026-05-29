"""コメントを事前生成して output/comments.csv に保存するバッチ。

実行:
    python -m scripts.generate_comments            # OpenAI API で生成
    python -m scripts.generate_comments --dry-run  # API を呼ばずダミー文を生成

現状はカテゴリごとに 1 つだけ生成するサンプル実装（レシピ情報は渡していない）。
"""

from __future__ import annotations

import argparse
import sys

from app import classifier, config, llm, storage

SYSTEM_PROMPT = """あなたは料理アプリ「おいしい健康」の編集者です。
ユーザーにレシピを薦める、自然で前向きな一言コメントを書きます。"""

USER_PROMPT_TEMPLATE = """次の条件で、レシピを薦める一言コメントを考えてください。

# 対象ユーザーのカテゴリ
{category_description}

# レシピ情報
{recipe_info}

# 出力のルール
- 日本語で 100 文字程度
- 前置きや「はい、」などの相づちは不要
"""


def build_messages(category_description: str, recipe_info: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                category_description=category_description,
                recipe_info=recipe_info,
            ),
        },
    ]


def generate_comment(category: str, recipe_info: str) -> str:
    messages = build_messages(classifier.describe_category(category), recipe_info)
    return llm.generate(messages)


def main() -> None:
    parser = argparse.ArgumentParser(description="コメントを事前生成して CSV に保存します。")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="OpenAI API を呼ばずにダミーのコメントを生成します（動作確認用）。",
    )
    args = parser.parse_args()

    if not args.dry_run and not llm.is_configured():
        print(
            "OPENAI_API_KEY が設定されていません。\n"
            "  - .env に API キーを設定するか、\n"
            "  - まずは `--dry-run` でパイプラインの動作を確認してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    rows: list[dict] = []
    for category in classifier.list_categories():
        # サンプルではレシピを指定せず、カテゴリごとに 1 つだけ生成する
        recipe_info = "（特定のレシピは指定なし。どんなレシピにも合う汎用的なコメントにしてください）"

        if args.dry_run:
            comment = f"[dry-run] カテゴリ{category}向けのサンプルコメントです。"
        else:
            comment = generate_comment(category, recipe_info)

        print(f"category={category}: {comment}")
        rows.append({"category": category, "comment": comment})

    storage.save_comments(rows)
    print(f"\n{len(rows)} 件のコメントを {config.COMMENTS_CSV} に保存しました。")


if __name__ == "__main__":
    main()
