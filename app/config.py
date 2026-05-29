"""パスや環境変数など、アプリ全体で使う設定値。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# .env を読み込む（OPENAI_API_KEY などを環境変数として使えるようにする）
load_dotenv()

# プロジェクトのルートディレクトリ（このファイルの 1 つ上の階層）
BASE_DIR = Path(__file__).resolve().parent.parent

# 配布データ（CSV）が置いてあるディレクトリ
DATA_DIR = BASE_DIR / "data"

# 生成物の出力先ディレクトリ（配布データと混ざらないよう data/ とは分ける）
OUTPUT_DIR = BASE_DIR / "output"

# 事前生成したコメントを保存する CSV ファイル
# （scripts/generate_comments.py が書き出し、API がここから読み出します）
COMMENTS_CSV = OUTPUT_DIR / "comments.csv"

# OpenAI の設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
