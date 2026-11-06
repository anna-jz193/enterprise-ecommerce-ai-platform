from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sellers = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_sellers_dataset.csv",
    dtype={
        "seller_id": "string",
        "seller_zip_code_prefix": "string",
    },
)

items = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_order_items_dataset.csv",
    dtype={
        "order_id": "string",
        "seller_id": "string",
    },
)

print("First 5 rows:")
print(sellers.head().to_string(index=False))

print("\nRows =", len(sellers))
print("Columns =", sellers.shape[1])
print("Unique seller_id =", sellers["seller_id"].nunique())

print("\nMissing seller_id =", sellers["seller_id"].isna().sum())
print("Duplicate seller_id =", sellers["seller_id"].duplicated().sum())
print("Duplicate entire rows =", sellers.duplicated().sum())

print("\nMissing values by column:")
print(sellers.isna().sum())

# check if seller exists in sellers?
invalid_seller_items = items.loc[
    ~items["seller_id"].isin(sellers["seller_id"])
]

print("\nItem rows with invalid seller foreign keys =",
      len(invalid_seller_items))

# show sellers that do not have any items in the order_items dataset
sellers_without_items = sellers.loc[
    ~sellers["seller_id"].isin(items["seller_id"])
]

print("Sellers without item records =", len(sellers_without_items))

print("\nSeller count by state:")
print(sellers["seller_state"].value_counts(dropna=False))

# check if an order involves multiple sellers
sellers_per_order = items.groupby("order_id")["seller_id"].nunique()

print("\nOrders with multiple sellers =",
      sellers_per_order.gt(1).sum())
print("Maximum sellers in one order =", sellers_per_order.max())



# finish seller information by joining items with sellers
item_sellers = items.merge(
    sellers,
    on="seller_id",
    how="left",
    validate="many_to_one",
)

print("\nItem rows after seller join =", len(item_sellers))

# per order, per seller, show item count, item total, freight total
order_seller_summary = (
    item_sellers.groupby(
        ["order_id", "seller_id"],
        as_index=False,
    )
    .agg(
        item_count=("order_item_id", "size"),
        items_total=("price", "sum"),
        freight_total=("freight_value", "sum"),
    )
)

print("\nOrder/seller summary rows =", len(order_seller_summary))

print("Duplicate order/seller pairs =",
      order_seller_summary.duplicated(
          subset=["order_id", "seller_id"]
      ).sum())

print("\nItem count preserved =",
      order_seller_summary["item_count"].sum() == len(items))

print("Item amount before aggregation =",
      round(items["price"].sum(), 2))
print("Item amount after aggregation =",
      round(order_seller_summary["items_total"].sum(), 2))

print("Freight before aggregation =",
      round(items["freight_value"].sum(), 2))
print("Freight after aggregation =",
      round(order_seller_summary["freight_total"].sum(), 2))