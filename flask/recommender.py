import json
from typing import List, Dict, Any

def load_products(path: str = "products.json") -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def score_product(prod: Dict[str, Any], top2: List[str]) -> int:
    """
    スコアリング：
      両方含む = +3
      どちらか含む = +1
      追加でカテゴリ数が少ない商品を優先（ニッチ度）
    """
    cats = set(prod.get("categories", []))
    tset = set(top2)
    inter = cats & tset
    base = 3 if len(inter) == 2 else (1 if len(inter) == 1 else 0)
    # ニッチ度（カテゴリが少ないほど +1 の可能性）
    niche_bonus = 1 if base > 0 and len(cats) <= 2 else 0
    return base + niche_bonus

def recommend(products: List[Dict[str, Any]], top2: List[str], limit: int = 8) -> List[Dict[str, Any]]:
    scored = []
    for p in products:
        s = score_product(p, top2)
        if s > 0:
            scored.append({
                "name": p.get("name"),
                "url": p.get("url"),
                "categories": p.get("categories", []),
                "coment": p.get("coment")  #kokotuika
            })
    # スコア→カテゴリ数(昇順)→名前 で安定ソート
    scored.sort(key=lambda x: (-x["score"], len(x["categories"]), x["name"]))
    return scored[:limit]
