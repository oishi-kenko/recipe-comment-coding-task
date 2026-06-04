"""API の簡単な動作確認テスト。

実行方法:
    pytest

サンプルとして最低限のテストだけ用意しています。
課題では、カテゴリ分類やフォールバックの挙動など、
ご自身の実装に合わせてテスト（または動作確認スクリプト）を追加してください。
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """ヘルスチェックが 200 を返し、ユーザー 100 人を読み込めている。"""
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["users"] == 100


def test_recipe_comment_returns_comment():
    """既存ユーザーへのリクエストで comment が返る。"""
    res = client.get("/recipe_comment", params={"user_id": "1", "recipe_id": "1691"})
    assert res.status_code == 200
    assert "comment" in res.json()
    assert isinstance(res.json()["comment"], str)


def test_unknown_user_falls_back():
    """存在しないユーザーでもフォールバックのコメントが返る（エラーにしない）。"""
    res = client.get("/recipe_comment", params={"user_id": "999999", "recipe_id": "1691"})
    assert res.status_code == 200
    assert res.json()["comment"]

def test_different_concerns_get_different_comments():
    """同じレシピでも、病態が違うユーザーには違うコメントが返る（出し分け）。"""
    res_a = client.get("/recipe_comment", params={"user_id": "67", "recipe_id": "1691"})
    res_b = client.get("/recipe_comment", params={"user_id": "26", "recipe_id": "1691"})
    assert res_a.json()["comment"] != res_b.json()["comment"]


def test_renal_user_is_classified_as_general():
    """腎臓系などの専門・少数の病態は、安全のため general に分類される。"""
    from app.classifier import classify_user
    user = {"concern_name": "透析", "cooking_skill": "中級"}
    category = classify_user(user)
    assert category.startswith("general")
