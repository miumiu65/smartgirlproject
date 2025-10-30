from flask import Flask, request, jsonify, render_template
import os, json
import main_cos
import catchcopy
import youtube
from flask_cors import CORS


# --- パス設定 ---
BASE_DIR = os.path.dirname(__file__)
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories_with_examples.json")
CATCH_JSON_PATH = os.path.join(BASE_DIR, "catchcopy.json")
PRODUCTS_PATH = os.path.join(BASE_DIR, "products.json")

# --- モデル・API設定 ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
MODEL_NAME = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")

# --- 商品データ読込 ---
with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

# --- キャッチコピー読込 ---
catchcopy.init(json_path=CATCH_JSON_PATH)

# --- モデル初期化 ---
print("🧠 モデル初期化中...", flush=True)
MODEL = main_cos.load_model(MODEL_NAME)
EXAMPLES = main_cos.load_category_examples(CATEGORIES_PATH)
CENTROIDS = main_cos.build_centroids(MODEL, EXAMPLES)
print("✅ モデル準備完了", flush=True)

# --- Flask設定 ---
app = Flask(__name__)  # templates/ フォルダを自動認識
CORS(app)


@app.route("/", methods=["GET", "POST"])
def index():
    youtube_service = youtube.get_authenticated_service()
    liked_videos = youtube.get_liked_videos(youtube_service)


    texts, videos = [], []
    for liked_video in liked_videos:
        try:
            info = main_cos.fetch_youtube_text(liked_video)
            texts.append(info["text"])
            videos.append({"url": info["url"], "title": info["title"]})
        except Exception as e:
            videos.append({"url": liked_video.get("url"), "title": None, "error": str(e)})

    # --- 動画テキストをまとめてAI分類 ---
    combined_text = " ".join(t for t in texts if t)
    return analyze(combined_text, videos)


def analyze(combined_text, videos):
    """AIで上位カテゴリを算出し、キャッチコピー＋推薦を生成"""
    # --- AIで上位カテゴリを推定 ---
    top2 = main_cos.classify_top2(MODEL, CENTROIDS, combined_text)  # e.g. [("ゲーム", 0.82), ("エンタメ", 0.76)]
    top2_names = [t[0] for t in top2][:2]
    result_str = " × ".join(top2_names) if top2_names else "(結果なし)"

    # --- キャッチコピー ---
    copy_text = catchcopy.get(top2_names[0], top2_names[1]) if len(top2_names) == 2 else None

    # --- 商品スコアリング ---
    def norm(s: str) -> str:
        return (s or "").strip().replace("　", " ").lower()

    tset = set(map(norm, top2_names))

    def score(prod) -> int:
        cats = set(map(norm, prod.get("categories", [])))
        hit = len(cats & tset)
        if hit == 0:
            return 0
        base = 3 if hit == 2 else 1       # 両方一致を優先
        niche = 1 if len(cats) <= 2 else 0  # カテゴリが少ない商品を優遇
        return base + niche

    scored = []
    for p in PRODUCTS:
        s = score(p)
        if s > 0:
            scored.append({**p, "score": s})

    # --- 並べ替え（スコア高い順 → カテゴリ少ない順）---
    scored.sort(key=lambda x: (-x["score"], len(x.get("categories", [])), x.get("name", "")))

    # --- JSONで返したい場合（APIモード）---
    if request.is_json:
        return jsonify({
            "ok": True,
            "top2": top2_names,
            "catchcopy": copy_text,
            "products": scored,
            "videos": videos
        })

    # --- HTMLで返す場合 ---
    return render_template(
        "index.html",
        result=result_str,
        catchcopy=copy_text,
        products=scored,
        videos=videos
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True, use_reloader=False)