"""ユーザーをカテゴリに分類する。

病態（concern_name）と料理スキルから、コメント生成・参照に使う
カテゴリのキーを決める。
"""

from __future__ import annotations

# --- 病態 → カテゴリの対応表 -------------------------------------------------
# 箱1: LLMに選ばせてよい病態（間違っても一般に落ちるだけで害が小さい）
_CONCERN_TO_CATEGORY = {
    # 減塩系
    "高血圧": "減塩",
    "血圧が高い": "減塩",
    "心筋梗塞": "減塩",
    "心不全": "減塩",
    # ダイエット系
    "ダイエット": "ダイエット",
    # 脂質系
    "脂質異常症": "脂質",
    "コレステロールが高い": "脂質",
    "中性脂肪が高い": "脂質",
    # 血糖系
    "糖尿病（2型）": "血糖",
    "血糖値・HbA1cが高い（糖尿病予備群）": "血糖",
    # 貧血・妊娠
    "貧血対策": "貧血",
    "妊娠中（後期）": "貧血",
    # 便秘
    "慢性便秘症": "便秘",
}

# 箱2: 安全のため必ず general に固定する病態（LLMに渡さない）
#   制限が中心で、LLMが逆方向の助言を書くリスクがあるもの
_FORCE_GENERAL = {
    "透析",
    "CKD（ステージ３a）",
    "腎機能の値が高い",
    "逆流性食道炎",
    "潰瘍性大腸炎（寛解期）",
}

# 箱1で扱う病態カテゴリ（general を除く）。generate 側でも使う。
_CONCERN_CATEGORIES = ["減塩", "ダイエット", "脂質", "血糖", "貧血", "便秘"]

# スキル2段階
_SKILL_TO_LEVEL = {
    "初心者": "easy",
    "初級": "easy",
    "中級": "skilled",
    "上級": "skilled",
}


def _concern_category(user: dict) -> str:
    """病態からカテゴリのベース部分を返す。"""
    concern = (user.get("concern_name") or "").strip()
    if concern in _FORCE_GENERAL:
        return "general"
    # 対応表になければ（健康予防・肌荒れ・欠損・想定外）一般に落とす
    return _CONCERN_TO_CATEGORY.get(concern, "general")


def _skill_level(user: dict) -> str:
    """スキルから easy / skilled を返す。欠損や想定外は easy 側に倒す。"""
    skill = (user.get("cooking_skill") or "").strip()
    return _SKILL_TO_LEVEL.get(skill, "easy")


def classify_user(user: dict) -> str:
    """ユーザー属性からカテゴリのキーを返す。

    形式は "<病態カテゴリ>__<スキル>" 。例: "減塩__easy"
    general は general__easy / general__skilled になる。
    """
    return f"{_concern_category(user)}__{_skill_level(user)}"


def list_categories() -> list[str]:
    """事前生成の対象となる全カテゴリの一覧。"""
    bases = _CONCERN_CATEGORIES + ["general"]
    levels = ["easy", "skilled"]
    return [f"{b}__{lv}" for b in bases for lv in levels]


def describe_category(category: str) -> str:
    """カテゴリのキーから、プロンプトに渡す説明文を返す。"""
    base, _, level = category.partition("__")
    concern_desc = {
        "減塩": "高血圧や心臓に配慮し、塩分控えめをうれしく感じる人",
        "ダイエット": "ダイエット中で、カロリー控えめ・高たんぱくに前向きな人",
        "脂質": "脂質やコレステロールの数値が気になり、管理したい人",
        "血糖": "血糖値が気になり、血糖を上げにくい食事を選びたい人",
        "貧血": "貧血対策や妊娠中で、鉄分などをしっかり摂りたい人",
        "便秘": "便秘がちで、食物繊維をしっかり摂りたい人",
        "general": "特別な制限はなく、バランスのよい食事をしたい人",
    }.get(base, "バランスのよい食事をしたい人")
    skill_desc = {
        "easy": "料理にあまり慣れておらず、手軽さや作りやすさを重視する",
        "skilled": "料理に慣れており、多少手間がかかっても気にしない",
    }.get(level, "")
    return f"{concern_desc}。調理面では、{skill_desc}。"