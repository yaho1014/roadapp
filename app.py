from flask import Flask, request, jsonify, render_template
import json
from pathlib import Path

app = Flask(__name__)

BASE = Path(__file__).parent

# =========================
# GeoJSON読み込み
# =========================
with open(BASE / "roads.geojson", "r", encoding="utf-8") as f:
    roads_geojson = json.load(f)

visited_file = BASE / "visited.csv"

visited = set()
if visited_file.exists():
    with open(visited_file, "r", encoding="utf-8") as f:
        next(f)
        for line in f:
            visited.add(line.strip())

# =========================
# visited付与
# =========================
def get_roads():

    data = roads_geojson

    for f in data["features"]:
        uid = str(f["properties"]["unique_id"])
        f["properties"]["visited"] = uid in visited

    return data

# =========================
# 画面
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# GeoJSON API
# =========================
@app.route("/roads")
def roads():
    return get_roads()

# =========================
# 仮最寄りAPI（まず安定優先）
# =========================
@app.route("/nearest", methods=["POST"])
def nearest():
    return jsonify({
        "road": "test",
        "id": "0000",
        "distance": 0
    })

# =========================
# 起動
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)