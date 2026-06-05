from pathlib import Path
import geopandas as gpd
import json

SHP_FILE = r"E:\ドキュメント\01_appdev\03_GISデータ\SHP\5339_test1_wgs84.shp"

BASE = Path(__file__).parent
OUT_FILE = BASE / "roads.geojson"

roads = gpd.read_file(SHP_FILE)
geojson = roads.to_crs(4326).__geo_interface__

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)

print("保存先:", OUT_FILE)