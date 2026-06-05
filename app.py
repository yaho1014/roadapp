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

# =========================
# visited読み込み
# =========================
visited_file = BASE / "visited.csv"

visited = set()

if visited_file.exists():
    with open(visited_file, "r", encoding="utf-8") as f:
        next(f, None)  # ヘッダー安全スキップ
        for line in f:
            visited.add(line.strip())


# =========================
# GeoJSONにvisitedフラグ付与
# =========================
def get_roads():

    data = json.loads(json.dumps(roads_geojson))  # コピー（安全化）

    for f in data["features"]:
        props = f.get("properties", {})
        uid = str(props.get("unique_id", ""))

        props["visited"] = uid in visited
        f["properties"] = props

    return data


# =========================
# 最寄りリンク検索（重要ロジック）
# =========================
from shapely.geometry import Point
import geopandas as gpd

# GeoJSONからGeoDataFrame作成（1回だけ）
roads = gpd.GeoDataFrame.from_features(roads_geojson["features"])
roads = roads.set_crs(4326)

roads_m = roads.to_crs(6677)


def get_nearest_link(lon, lat):

    point = Point(lon, lat)
    point_m = gpd.GeoSeries([point], crs="EPSG:4326").to_crs(6677).iloc[0]

    roads_m["distance"] = roads_m.distance(point_m)

    idx = roads_m["distance"].idxmin()

    nearest = roads.iloc[idx]
    dist = roads_m.loc[idx, "distance"]

    return nearest, dist


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
def roads_api():
    return jsonify(get_roads())


# =========================
# 現在地→最寄り国道
# =========================
@app.route("/nearest", methods=["POST"])
def nearest():

    data = request.json
    lon = data["lon"]
    lat = data["lat"]

    nearest, dist = get_nearest_link(lon, lat)

    return jsonify({
        "road": str(nearest.get("rosen_name", "")),
        "id": str(nearest.get("route_id", "")),
        "distance": float(dist)
    })


# =========================
# 起動
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)