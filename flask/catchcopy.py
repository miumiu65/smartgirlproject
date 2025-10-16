# catchcopy.py
import json, unicodedata, re

_mapping = {}

def _norm(s: str) -> str:
    # 全角→半角などの正規化 + スペース畳み込み
    x = unicodedata.normalize("NFKC", (s or "")).strip()
    x = x.replace("\u3000", " ")          # 全角空白→半角
    x = re.sub(r"\s+", " ", x)            # 連続空白を1つに
    return x

def init(json_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    global _mapping
    _mapping = {
        frozenset((_norm(i["a"]), _norm(i["b"]))): i["copy"].strip()
        for i in data
        if i.get("a") and i.get("b") and i.get("copy")
    }

def get(a: str, b: str) -> str | None:
    return _mapping.get(frozenset((_norm(a), _norm(b))))