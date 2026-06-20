from flask import Flask, request, jsonify, render_template
import json
from pathlib import Path
from datetime import datetime

from shapely.geometry import Point
import geopandas as gpd

app = Flask(__name__)

BASE = Path(__file__).parent

# =========================
# GeoJSON読み込み
# =========================
roads = gpd.read_file(
    BASE / "roads_kanto_wbs84.gpkg",
    layer="roads_kanto_wbs84"
)

# =========================
# リンクID生成
# 路線番号_連番
# =========================
roads["link_id"] = [
    f"{roads.iloc[i]['rosen_name']}_{i+1:06d}"
    for i in range(len(roads))
]


# =========================
# visited.csv
# =========================
visited_file = BASE / "visited.csv"
gps_log_file = BASE / "gps_log.csv"


def load_visited():

    result = set()

    if visited_file.exists():

        with open(visited_file, "r", encoding="utf-8") as f:

            next(f, None)

            for line in f:

                value = line.strip()

                if value:
                    result.add(value)

    return result


# =========================
# GeoJSONにvisited付与
# =========================
def get_roads():

    visited = load_visited()

    data = json.loads(
        roads.to_json()
    )

    for feature in data["features"]:

        uid = feature["properties"].get(
            "link_id",
            ""
        )

        feature["properties"]["visited"] = (
            uid in visited
        )

    return data


# =========================
# GeoDataFrame生成
# =========================
#roads = gpd.read_file(
#    BASE / "roads_kanto_wbs84.gpkg",
#    layer="roads_kanto_wbs84"
#)

roads["link_id"] = [
    f"{roads.iloc[i]['rosen_name']}_{i+1:06d}"
    for i in range(len(roads))
]

roads_m = roads.to_crs(6677)

roads_m["length_m"] = roads_m.length


# =========================
# 最寄りリンク検索
# =========================
def get_nearest_link(lon, lat):

    point = Point(lon, lat)

    point_m = (
        gpd.GeoSeries(
            [point],
            crs="EPSG:4326"
        )
        .to_crs(6677)
        .iloc[0]
    )

    roads_m["distance"] = roads_m.distance(point_m)

    idx = roads_m["distance"].idxmin()

    nearest = roads.iloc[idx]

    dist = float(
        roads_m.loc[idx, "distance"]
    )

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

    west = float(request.args.get("west"))
    east = float(request.args.get("east"))
    south = float(request.args.get("south"))
    north = float(request.args.get("north"))

    subset = roads.cx[
        west:east,
        south:north
    ]

    data = json.loads(
        subset.to_json()
    )

    visited = load_visited()

    for feature in data["features"]:

        uid = feature["properties"].get(
            "link_id",
            ""
        )

        feature["properties"]["visited"] = (
            uid in visited
        )

    return jsonify(data)

# =========================
# 最寄り道路取得
# =========================
@app.route("/nearest", methods=["POST"])
def nearest():

    data = request.json

    lon = data["lon"]
    lat = data["lat"]

    nearest_link, dist = get_nearest_link(
        lon,
        lat
    )

    return jsonify({
        "road": str(
            nearest_link.get(
                "rosen_name",
                ""
            )
        ),
        "link_id": str(
            nearest_link["link_id"]
        ),
        "distance": dist
    })


# =========================
# 踏破登録
# =========================
@app.route("/visit", methods=["POST"])
def visit():

    data = request.json

    lon = data["lon"]
    lat = data["lat"]

    nearest_link, dist = get_nearest_link(
        lon,
        lat
    )

    uid = str(
        nearest_link["link_id"]
    )

    visited = load_visited()

    already = uid in visited

    if not already:

        new_file = not visited_file.exists()

        with open(
            visited_file,
            "a",
            encoding="utf-8"
        ) as f:

            if new_file:
                f.write("link_id\n")

            f.write(uid + "\n")

    return jsonify({
        "status": "ok",
        "already": already,
        "link_id": uid,
        "distance": dist
    })


@app.route("/gps_log")
def gps_log():

    points = []

    if gps_log_file.exists():

        with open(
            gps_log_file,
            "r",
            encoding="utf-8"
        ) as f:

            next(f, None)

            for line in f:

                parts = line.strip().split(",")

                if len(parts) != 3:
                    continue

                points.append({
                    "lat": float(parts[1]),
                    "lon": float(parts[2])
                })

    return jsonify(points)


# =========================
# 踏破数確認
# =========================
@app.route("/stats")
def stats():

    visited = load_visited()

    return jsonify({
        "visited_count": len(visited)
    })

@app.route("/progress")
def progress():

    visited = load_visited()

    total_length = roads_m["length_m"].sum()

    visited_length = roads_m[
        roads["link_id"].isin(visited)
    ]["length_m"].sum()

    percent = 0

    if total_length > 0:
        percent = (
            visited_length
            / total_length
            * 100
        )

    return jsonify({
        "visited_m": round(
            float(visited_length), 1
        ),
        "total_m": round(
            float(total_length), 1
        ),
        "percent": round(
            float(percent), 1
        )
    })

# =========================
# GPSログ保存
# =========================
@app.route("/log", methods=["POST"])
def log_position():

    data = request.json

    lat = data["lat"]
    lon = data["lon"]

    new_file = not gps_log_file.exists()

    with open(
        gps_log_file,
        "a",
        encoding="utf-8"
    ) as f:

        if new_file:
            f.write(
                "timestamp,lat,lon\n"
            )

        f.write(
            f"{datetime.now().isoformat()},{lat},{lon}\n"
        )

    return jsonify({
        "status": "ok"
    })


# =========================
# GPSログ件数
# =========================
@app.route("/log_stats")
def log_stats():

    count = 0

    if gps_log_file.exists():

        with open(
            gps_log_file,
            "r",
            encoding="utf-8"
        ) as f:

            next(f, None)

            for _ in f:
                count += 1

    return jsonify({
        "count": count
    })

# =========================
# 起動
# =========================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000,
        debug=True
    )