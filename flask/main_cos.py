import os, json, re, numpy as np, requests
from urllib.parse import urlparse, parse_qs
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ===== モデル =====
def load_model(model_name: str = "intfloat/multilingual-e5-large") -> SentenceTransformer:
    print(f"📦 モデル読み込み中: {model_name}", flush=True)
    return SentenceTransformer(model_name)

# ===== カテゴリ重心 =====
def load_category_examples(path: str) -> dict[str, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_centroids(model: SentenceTransformer, examples: dict[str, list[str]]) -> dict[str, np.ndarray]:
    centroids: dict[str, np.ndarray] = {}
    for label, texts in examples.items():
        texts = [t for t in texts if isinstance(t, str) and t.strip()]
        if not texts:
            continue
        embs = model.encode(texts)  # [n, d]
        centroids[label] = embs.mean(axis=0)
    return centroids

# エンドポイント
def classify_vector(model, centroids: dict[str, np.ndarray], vector: list[float], top_k: int = 2):
    v = np.asarray(vector, dtype=np.float32).reshape(1, -1)
    sims = []
    for label, c in centroids.items():
        score = float(cosine_similarity(v, [c])[0][0])
        sims.append({"label": label, "score": score})
    sims.sort(key=lambda x: x["score"], reverse=True)
    return sims[:max(1, top_k)]
# ===== 分類 =====
def classify_top2(model: SentenceTransformer, centroids: dict[str, np.ndarray], text: str):
    v = model.encode([text])[0]
    sims = []
    for label, c in centroids.items():
        score = float(cosine_similarity([v], [c])[0][0])
        sims.append((label, score))
    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:2]   # 上位2件


# ===== YouTube 情報取得 =====
def _video_id(url: str) -> str | None:
    p = urlparse(url)
    q = parse_qs(p.query).get("v")
    if q: return q[0]
    pid = p.path.strip("/").split("/")[-1]
    return pid or None

def fetch_youtube_text(data) -> dict:
    if not data.get("snippet"):
        raise ValueError(f"動画が見つかりませんでした。")
    s = data["snippet"]
    vid = s.get("id")
    url = ""
    title = s.get("title", "")
    desc = s.get("description", "") or ""
    tags = s.get("tags", []) or []
    text = f"{title}。{desc} {' '.join(tags)}"
    return {"video_id": vid, "title": title, "description": desc, "tags": tags, "text": text, "url": url}

def fetch_youtube_text_org(api_key: str, url: str) -> dict:
    vid = _video_id(url)
    if not vid:
        raise ValueError("URLから動画IDを抽出できませんでした。")
    r = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"part": "snippet", "id": vid, "key": api_key},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("items"):
        raise ValueError(f"動画ID {vid} が見つかりませんでした。")
    s = data["items"][0]["snippet"]
    title = s.get("title", "")
    desc = s.get("description", "") or ""
    tags = s.get("tags", []) or []
    text = f"{title}。{desc} {' '.join(tags)}"
    return {"video_id": vid, "title": title, "description": desc, "tags": tags, "text": text, "url": url}
