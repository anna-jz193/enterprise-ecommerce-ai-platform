from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

products = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_products_dataset.csv",
    dtype={"product_id": "string"},
)

items = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_order_items_dataset.csv",
    dtype={
        "order_id": "string",
        "product_id": "string",
    },
)

print("First 5 rows:")
print(products.head().to_string(index=False))

print("\nRows =", len(products))
print("Columns =", products.shape[1])
print("Unique product_id =", products["product_id"].nunique())

print("\nMissing product_id =", products["product_id"].isna().sum())
print("Duplicate product_id =", products["product_id"].duplicated().sum())
print("Duplicate entire rows =", products.duplicated().sum())

print("\nMissing values by column:")
print(products.isna().sum())

# 1. check if product exists in products?
invalid_product_items = items.loc[
    ~items["product_id"].isin(products["product_id"])
]

print("\nItem rows with invalid product foreign keys =",
      len(invalid_product_items))

print("\nDistinct categories =",
      products["product_category_name"].nunique())

print("\nTop 10 categories by product count:")
print(
    products["product_category_name"]
    .value_counts(dropna=False)
    .head(10)
)

print("\nNumeric column summary:")
print(products.describe().to_string())



# 1. check for missing metadata fields
metadata_cols = [
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
]

metadata_missing = products[metadata_cols].isna()

print("\nProducts missing any metadata field =",
      metadata_missing.any(axis=1).sum())
print("Products missing all four metadata fields =",
      metadata_missing.all(axis=1).sum())

# 2. check for missing physical fields
physical_cols = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

physical_missing = products[physical_cols].isna()

print("\nProducts missing any physical field =",
      physical_missing.any(axis=1).sum())
print("Products missing all four physical fields =",
      physical_missing.all(axis=1).sum())

# 3. check for zero weight, negative weight, and non-positive dimensions
print("\nZero-weight products =",
      products["product_weight_g"].eq(0).sum())
print("Negative-weight products =",
      products["product_weight_g"].lt(0).sum())

dimension_cols = [
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

print("\nNon-positive dimensions by column:")
print(products[dimension_cols].le(0).sum())

# 4. join product attributes to order items, keeping each item as a row
item_products = items.merge(
    products[
        ["product_id", "product_category_name"] + physical_cols
    ],
    on="product_id",
    how="left",
    validate="many_to_one",
)

print("\nItem rows after product join =", len(item_products))

missing_category = item_products["product_category_name"].isna()

print("\nItem rows with missing category =", missing_category.sum())
print("Distinct orders containing missing-category products =",
      item_products.loc[missing_category, "order_id"].nunique())

missing_physical = item_products[physical_cols].isna().any(axis=1)

print("\nItem rows with missing physical attributes =",
      missing_physical.sum())

print("Item rows with zero product weight =",
      item_products["product_weight_g"].eq(0).sum())



products_clean = products.copy()

# create flags for missing in copy
products_clean["is_category_missing"] = (
    products_clean["product_category_name"].isna()
)

products_clean["is_metadata_missing"] = (
    products_clean[metadata_cols].isna().all(axis=1)
)

products_clean["is_physical_missing"] = (
    products_clean[physical_cols].isna().any(axis=1)
)

products_clean["is_weight_zero"] = (
    products_clean["product_weight_g"].eq(0)
)

# create a separate column for reporting categories, avoiding overwriting the original
products_clean["category_for_reporting"] = (
    products_clean["product_category_name"].fillna("unknown")
)

print("\nProduct quality flags:")
print(
    products_clean[
        [
            "is_category_missing",
            "is_metadata_missing",
            "is_physical_missing",
            "is_weight_zero",
        ]
    ].sum()
)

print("\nProducts retained =", len(products_clean))
print(
    "Missing reporting categories =",
    products_clean["category_for_reporting"].isna().sum(),
)


translations = pd.read_csv(
    PROJECT_ROOT / "data" / "raw"
    / "product_category_name_translation.csv",
    dtype="string",
)

print("\nTranslation sample:")
print(translations.head().to_string(index=False))

print("\nTranslation rows =", len(translations))

print("\nMissing translation values:")
print(translations.isna().sum())

print("\nDuplicate source categories =",
      translations["product_category_name"].duplicated().sum())

# check for missing source categories in the translation table
if translations["product_category_name"].isna().any():
    raise ValueError("Translation table contains missing source categories.")

products_en = products_clean.merge(
    translations,
    on="product_category_name",
    how="left",
    validate="many_to_one",
    indicator="translation_match",
)

# check for missing translations in the products dataset
unmapped = (
    products_en["product_category_name"].notna()
    & products_en["translation_match"].eq("left_only")
)

print("\nProducts after translation join =", len(products_en))

print("\nProducts with missing source category =",
      products_en["is_category_missing"].sum())

print("Products with unmapped source category =", unmapped.sum())

print("\nUnmapped categories by product count:")
print(
    products_en.loc[unmapped, "product_category_name"]
    .value_counts()
)


products_en["is_translation_unmapped"] = unmapped

# english first, then fallback to original category, and finally "unknown" if both are missing
products_en["category_for_reporting"] = (
    products_en["product_category_name_english"]
    .fillna(products_en["product_category_name"])
    .fillna("unknown")
)

print("\nReporting category checks:")
print("Products retained =", len(products_en))
print("Missing reporting categories =",
      products_en["category_for_reporting"].isna().sum())
print("Unmapped translation products =",
      products_en["is_translation_unmapped"].sum())

print("\nFallback categories:")
print(
    products_en.loc[
        products_en["is_translation_unmapped"],
        ["product_category_name", "category_for_reporting"],
    ].drop_duplicates().to_string(index=False)
)