import React, { useState } from "react";
import './App.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [top2, setTop2] = useState([]);
  const [copy, setCopy] = useState("");
  const [items, setItems] = useState([]);
  const [videos, setVideos] = useState([]);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requestFrom: "react" }), // Flask側のrequest.is_json用
      });
      const data = await res.json();
      if (data.ok) {
        setTop2(data.top2 || []);
        setCopy(data.catchcopy || "");
        setItems(data.products || []);
        setVideos(data.videos || []);
      } else {
        alert("サーバーエラー: " + (data.error || "不明"));
      }
    } catch (err) {
      console.error(err);
      alert("通信エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>🎬 SmartGirl Project</h1>
      <button
        onClick={handleAnalyze}
        disabled={loading}
        style={{
          padding: "10px 20px",
          background: "#ff4d0a",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
        }}
      >
        {loading ? "分析中..." : "AI分析を開始"}
      </button>

      {top2.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2>あなたのタイプ</h2>
          <p style={{ fontSize: "1.2rem", fontWeight: "bold" }}>
            {top2.join(" × ")}
          </p>
          <p>{copy}</p>
        </div>
      )}

      {items.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2>おすすめ商品</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "1rem",
            }}
          >
            {items.map((p, i) => (
              <div
                key={i}
                style={{
                  border: "1px solid #ddd",
                  borderRadius: "8px",
                  padding: "1rem",
                  background: "#fffaf8",
                }}
              >
                <h3>{p.name}</h3>
                <p>カテゴリ: {p.categories.join(", ")}</p>
                {p.coment && <p>💬 {p.coment}</p>}
                <a href={p.url} target="_blank" rel="noreferrer">
                  商品を見る
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {videos.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2>あなたの高評価動画</h2>
          <ul>
            {videos.map((v, i) => (
              <li key={i}>
                <a href={v.url} target="_blank" rel="noreferrer">
                  {v.title || "タイトルなし"}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;