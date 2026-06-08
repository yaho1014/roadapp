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
with open(BASE / "roads.geojson", "r", encoding="utf-8") as f:
    roads_geojson = json.load(f)

# =========================
# リンクID生成
# 路線番号_連番
# =========================
for i, feature in enumerate(
    roads_geojson["features"],
    start=1
):
    props = feature["properties"]

    props["link_id"] = (
        f"{props.get('rosen_name','0')}"
        f"_{i:06d}"
    )

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

    data = json.loads(json.dumps(roads_geojson))

    for feature in data["features"]:

        props = feature.get("properties", {})

        uid = str(props.get("link_id", ""))

        props["visited"] = uid in visited

        feature["properties"] = props

    return data


# =========================
# GeoDataFrame生成
# =========================
roads = gpd.GeoDataFrame.from_features(
    roads_geojson["features"]
)

roads = roads.set_crs(4326)

roads_m = roads.to_crs(6677)


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

    return jsonify(
        get_roads()
    )


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


# =========================
# 踏破数確認
# =========================
@app.route("/stats")
def stats():

    visited = load_visited()

    return jsonify({
        "visited_count": len(visited)
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