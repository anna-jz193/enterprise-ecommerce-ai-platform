from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

items = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_order_items_dataset.csv",
    dtype={
        "order_id": "string",
        "order_item_id": "Int64",
        "product_id": "string",
        "seller_id": "string",
    },
)

print("First 5 rows:")
print(items.head().to_string(index=False))

print("\nRows =", len(items))
print("Columns =", items.shape[1])

print("\nColumn names:")
print(items.columns.tolist())

print("\nUnique order_id =", items["order_id"].nunique())
print("Unique order_item_id =", items["order_item_id"].nunique())

print(
    "Duplicate order/item pairs =",
    items.duplicated(subset=["order_id", "order_item_id"]).sum(),
)

print("Duplicate entire rows =", items.duplicated().sum())

print("\nMissing values by column:")
print(items.isna().sum())


orders = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_orders_dataset.csv",
    dtype={"order_id": "string"},
)

# 1. check if order exists in orders?
invalid_item_orders = items.loc[
    ~items["order_id"].isin(orders["order_id"])
]

print("\nItem rows with invalid order foreign keys =",
      len(invalid_item_orders))

# 2. show orders that do not have any items in the order_items dataset
orders_without_items = orders.loc[
    ~orders["order_id"].isin(items["order_id"])
]

print("\nOrders without items =", len(orders_without_items))

print("\nStatus of orders without items:")
print(orders_without_items["order_status"].value_counts())

# 3. show the number of items for each order that has items
items_per_order = items.groupby("order_id").size()

print("\nItems per order summary:")
print(items_per_order.describe())

print("\nOrders with multiple items =",
      (items_per_order > 1).sum())


# solve problem of orders without items
# 1. row group by order_id to get item count, total price, total freight
order_item_summary = (
    items.groupby("order_id", as_index=False)
    .agg(
        item_count=("order_item_id", "size"),
        items_total=("price", "sum"),
        freight_total=("freight_value", "sum"),
    )
)

# 2. keep all orders, even those without items, and merge with the order_item_summary
order_summary = orders.merge(
    order_item_summary,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator=True,
)

# 3. clearly mark whether each order has items
order_summary["has_items"] = order_summary["_merge"].eq("both")
order_summary = order_summary.drop(columns="_merge")

print("\nRows after merge =", len(order_summary))
print("Unique orders after merge =",
      order_summary["order_id"].nunique())

print("\nHas items:")
print(order_summary["has_items"].value_counts())

print("\nSample order summary:")
print(
    order_summary[
        [
            "order_id",
            "order_status",
            "item_count",
            "items_total",
            "freight_total",
            "has_items",
        ]
    ].head().to_string(index=False)
)


# Reasonableness check for the amounts
# check the price and freight values in the order_items dataset
print("\nPrice and freight summary:")
print(items[["price", "freight_value"]].describe())

# check for negative or zero values in price and freight
print("\nNegative prices =", (items["price"] < 0).sum())
print("Zero prices =", (items["price"] == 0).sum())

print("Negative freight =", (items["freight_value"] < 0).sum())
print("Zero freight =", (items["freight_value"] == 0).sum())

# Reasonableness check for the amounts
print("\nItem price total before aggregation =",
      round(items["price"].sum(), 2))
print("Item price total after merge =",
      round(order_summary["items_total"].sum(min_count=1), 2))

print("\nFreight total before aggregation =",
      round(items["freight_value"].sum(), 2))
print("Freight total after merge =",
      round(order_summary["freight_total"].sum(min_count=1), 2))