# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# --- 設定 ---
BASE_DIR = os.path.dirname(__file__)
PRODUCTS_PATH = os.path.join(BASE_DIR, "products.json")

# --- データ読込 ---
def load_products(path=PRODUCTS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

PRODUCTS = load_products()


# --- 正規化とスコア計算 ---
def norm(cat: str) -> str:
    """全角/半角スペースや大文字小文字の違いを吸収"""
    return (cat or "").strip().replace("　", " ").lower()


def score_product(prod, top2):
    """カテゴリ一致数でスコアを付ける"""
    cats = [norm(c) for c in prod.get("categories", [])]
    t2 = [norm(c) for c in top2]
    hit = len(set(cats) & set(t2))
    if hit == 2:
        base = 3
    elif hit == 1:
        base = 1
    else:
        base = 0
    niche = 1 if base > 0 and len(cats) <= 2 else 0
    return base + niche


# --- APIエンドポイント ---
@app.post("/recommend")
def recommend_api():
    """
    JSON 形式で上位2カテゴリを受け取り、マッチした商品を返す。
    例:
      POST /recommend
      { "top2": ["ゲーム", "エンタメ"], "limit": 5 }
    """
    try:
        body = request.get_json(force=True) or {}
        top2 = body.get("top2") or []
        limit = int(body.get("limit") or 8)

        if not isinstance(top2, list) or len(top2) == 0:
            return jsonify({"ok": False, "error": "top2 を ['カテゴリA','カテゴリB'] の形で渡してください"}), 400

        scored = []
        for p in PRODUCTS:
            s = score_product(p, top2[:2])
            if s > 0:
                scored.append({
                    "name": p.get("name"),
                    "url": p.get("url"),
                    "categories": p.get("categories", []),
                    "sdgs": p.get("sdgs", []),
                    "score": s
                })

        scored.sort(key=lambda x: (-x["score"], len(x["categories"]), x["name"]))

        return jsonify({
            "ok": True,
            "top2": top2[:2],
            "count": len(scored),
            "items": scored[:limit]
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"server-error: {type(e).__name__}: {e}"
        }), 500


# --- 起動 ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
