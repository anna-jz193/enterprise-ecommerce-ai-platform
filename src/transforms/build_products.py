from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

products = pd.read_csv(
    RAW_DIR / "olist_products_dataset.csv",
    dtype={"product_id": "string", "product_category_name": "string"},
)

translations = pd.read_csv(
    RAW_DIR / "product_category_name_translation.csv",
    dtype="string",
)

# check input
if products["product_id"].isna().any():
    raise ValueError("Products contains missing product IDs.")

if products["product_id"].duplicated().any():
    raise ValueError("Products contains duplicate product IDs.")

if translations.isna().any().any():
    raise ValueError("Translation table contains missing values.")

if translations["product_category_name"].duplicated().any():
    raise ValueError("Translation table contains duplicate source categories.")

metadata_cols = [
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
]

physical_cols = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

result = products.merge(
    translations,
    on="product_category_name",
    how="left",
    validate="many_to_one",
    indicator="translation_match",
)

# 应用已确认的质量标记
result["is_category_missing"] = result["product_category_name"].isna()
result["is_metadata_missing"] = result[metadata_cols].isna().all(axis=1)
result["is_physical_missing"] = result[physical_cols].isna().any(axis=1)
result["is_weight_zero"] = result["product_weight_g"].eq(0)

result["is_translation_unmapped"] = (
    result["product_category_name"].notna()
    & result["translation_match"].eq("left_only")
)

result["category_for_reporting"] = (
    result["product_category_name_english"]
    .fillna(result["product_category_name"])
    .fillna("unknown")
)

result = result.drop(columns="translation_match")

# 输出检查
if len(result) != len(products):
    raise ValueError("Product row count changed during transformation.")

if result["category_for_reporting"].isna().any():
    raise ValueError("Reporting categories contain missing values.")

# 检查通过后才写入文件
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
output_path = OUTPUT_DIR / "dim_products.csv"

result.to_csv(output_path, index=False)

print("Products written =", len(result))
print("Unique product IDs =", result["product_id"].nunique())
print("Unmapped translation products =",
      result["is_translation_unmapped"].sum())
print("Saved to:", output_path)