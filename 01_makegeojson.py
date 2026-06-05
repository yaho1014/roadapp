from pathlib import Path
import geopandas as gpd
import json

SHP_FILE = r"E:\ドキュメント\01_appdev\03_GISデータ\SHP\5339_test1_wgs84.shp"

BASE = Path(__file__).parent
OUT_FILE = BASE / "roads.geojson"

roads = gpd.read_file(SHP_FILE)

# =========================
# ★ 追加：属性チェック（先頭5件）
# =========================
print("\n===== 属性サンプル（先頭5行）=====")
print(roads.head(5))

print("\n===== カラム一覧 =====")
print(list(roads.columns))

# =========================
# GeoJSON変換
# =========================
geojson = roads.to_crs(4326).__geo_interface__

# =========================
# 保存
# =========================
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)

print("\n保存先:", OUT_FILE)
print("features数:", len(geojson["features"]))