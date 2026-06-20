from pathlib import Path
import geopandas as gpd
import json
from tkinter import Tk, filedialog

# =========================
# SHP選択
# =========================
root = Tk()
root.withdraw()

SHP_FILE = filedialog.askopenfilename(
    title="Shapefileを選択",
    filetypes=[("Shapefile", "*.shp")]
)

if not SHP_FILE:
    print("ファイルが選択されませんでした")
    exit()

print("選択ファイル:", SHP_FILE)

# =========================
# 読み込み
# =========================
roads = gpd.read_file(SHP_FILE)

# =========================
# 属性確認
# =========================
print("\n===== 属性サンプル（先頭5行）=====")
print(roads.head())

print("\n===== カラム一覧 =====")
print(list(roads.columns))

# =========================
# GeoJSON出力先
# =========================
BASE = Path(__file__).parent
OUT_FILE = BASE / "roads.geojson"

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