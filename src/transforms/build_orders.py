from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

orders = pd.read_csv(
    RAW_DIR / "olist_orders_dataset.csv",
    dtype={"order_id": "string", "customer_id": "string"},
)

items = pd.read_csv(
    RAW_DIR / "olist_order_items_dataset.csv",
    dtype={
        "order_id": "string",
        "seller_id": "string",
    },
)

# input checks
if orders["order_id"].isna().any():
    raise ValueError("Orders contains missing order IDs.")

if orders["order_id"].duplicated().any():
    raise ValueError("Orders contains duplicate order IDs.")

item_keys = ["order_id", "order_item_id"]

if items[item_keys].isna().any().any():
    raise ValueError("Items contains missing key values.")

if items.duplicated(subset=item_keys).any():
    raise ValueError("Items contains duplicate order/item pairs.")

if not items["order_id"].isin(orders["order_id"]).all():
    raise ValueError("Items contains order IDs absent from Orders.")

# summary 
item_summary = (
    items.groupby("order_id", as_index=False)
    .agg(
        item_count=("order_item_id", "size"),
        seller_count=("seller_id", "nunique"),
        items_total=("price", "sum"),
        freight_total=("freight_value", "sum"),
    )
)

result = orders.merge(
    item_summary,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator="item_match",
)

result["has_items"] = result["item_match"].eq("both")
result = result.drop(columns="item_match")

if len(result) != len(orders):
    raise ValueError("Order row count changed.")

print("Order rows =", len(result))
print("Unique order IDs =", result["order_id"].nunique())

print("\nHas items:")
print(result["has_items"].value_counts())

print("\nOrders with multiple sellers =",
      result["seller_count"].gt(1).sum())


# part 2
# result
payments = pd.read_csv(
    RAW_DIR / "olist_order_payments_dataset.csv",
    dtype={
        "order_id": "string",
        "payment_sequential": "Int64",
        "payment_installments": "Int64",
    },
)

# check input
payment_keys = ["order_id", "payment_sequential"]

if payments[payment_keys].isna().any().any():
    raise ValueError("Payments contains missing key values.")

if payments.duplicated(subset=payment_keys).any():
    raise ValueError("Payments contains duplicate order/payment pairs.")

if not payments["order_id"].isin(orders["order_id"]).all():
    raise ValueError("Payments contains order IDs absent from Orders.")

if payments["payment_value"].isna().any():
    raise ValueError("Payments contains missing amounts.")

if payments["payment_value"].lt(0).any():
    raise ValueError("Payments contains negative amounts.")

# keep original data and create flags
payments["is_zero_payment"] = payments["payment_value"].eq(0)
payments["is_undefined_type"] = payments["payment_type"].eq("not_defined")
payments["is_zero_installments"] = payments["payment_installments"].eq(0)

payment_summary = (
    payments.groupby("order_id", as_index=False)
    .agg(
        payment_record_count=("payment_sequential", "size"),
        payment_total=("payment_value", "sum"),
        has_zero_payment=("is_zero_payment", "any"),
        has_undefined_type=("is_undefined_type", "any"),
        has_zero_installments=("is_zero_installments", "any"),
    )
)

result = result.merge(
    payment_summary,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator="payment_match",
)

result["has_payment_record"] = result["payment_match"].eq("both")
result = result.drop(columns="payment_match")

# convert amounts to integers in cents for comparison, keeping missing values
payment_cents = result["payment_total"].mul(100).round().astype("Int64")
item_cents = result["items_total"].mul(100).round().astype("Int64")
freight_cents = result["freight_total"].mul(100).round().astype("Int64")

result["difference_cents"] = payment_cents - item_cents - freight_cents

comparable = result["has_items"] & result["has_payment_record"]

result["amount_check"] = "not_comparable"
result.loc[comparable, "amount_check"] = "within_tolerance"

mismatch = (
    comparable
    & result["difference_cents"].abs().gt(1).fillna(False)
)
result.loc[mismatch, "amount_check"] = "mismatch"

if len(result) != len(orders):
    raise ValueError("Order row count changed after payment join.")

# keep unknowns as a separate category for reporting
payment_flags = [
    "has_zero_payment",
    "has_undefined_type",
    "has_zero_installments",
]
result[payment_flags] = result[payment_flags].astype("boolean")

print("\nRows after payment join =", len(result))

print("\nHas payment record:")
print(result["has_payment_record"].value_counts())

print("\nAmount check:")
print(result["amount_check"].value_counts())

print("\nPayment total before aggregation =",
      round(payments["payment_value"].sum(), 2))
print("Payment total after join =",
      round(result["payment_total"].sum(min_count=1), 2))


# part 3
reviews = pd.read_csv(
    RAW_DIR / "olist_order_reviews_dataset.csv",
    dtype={"review_id": "string", "order_id": "string"},
)

# input checks
review_keys = ["review_id", "order_id"]

if reviews[review_keys].isna().any().any():
    raise ValueError("Reviews contains missing key values.")

if reviews.duplicated(subset=review_keys).any():
    raise ValueError("Reviews contains duplicate review/order pairs.")

if not reviews["order_id"].isin(orders["order_id"]).all():
    raise ValueError("Reviews contains order IDs absent from Orders.")

if not reviews["review_score"].isin([1, 2, 3, 4, 5]).all():
    raise ValueError("Reviews contains missing or invalid scores.")

reviews["has_comment_message"] = (
    reviews["review_comment_message"]
    .astype("string")
    .fillna("")
    .str.strip()
    .ne("")
)

# keep all reviews and aggregate by order_id
review_summary = (
    reviews.groupby("order_id", as_index=False)
    .agg(
        review_count=("review_id", "size"),
        review_score_mean=("review_score", "mean"),
        review_score_min=("review_score", "min"),
        review_score_max=("review_score", "max"),
        has_review_message=("has_comment_message", "any"),
    )
)

review_summary["has_score_disagreement"] = (
    review_summary["review_score_min"]
    != review_summary["review_score_max"]
)

result = result.merge(
    review_summary,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator="review_match",
)

result["has_review_record"] = result["review_match"].eq("both")
result = result.drop(columns="review_match")

# signal unknowns
review_flags = ["has_review_message", "has_score_disagreement"]
result[review_flags] = result[review_flags].astype("boolean")

# count columns to be converted to nullable integers
count_cols = [
    "item_count",
    "seller_count",
    "payment_record_count",
    "review_count",
]
result[count_cols] = result[count_cols].astype("Int64")

# final checks
if len(result) != len(orders):
    raise ValueError("Final order row count changed.")

if result["order_id"].isna().any() or result["order_id"].duplicated().any():
    raise ValueError("Final order IDs are missing or duplicated.")

if result["review_count"].sum() != len(reviews):
    raise ValueError("Review count was not preserved.")

print("\nFinal order rows =", len(result))
print("Unique order IDs =", result["order_id"].nunique())

print("\nHas review record:")
print(result["has_review_record"].value_counts())

print("\nOrders with differing review scores =",
      result["has_score_disagreement"].sum())

# output
output_dir = PROJECT_ROOT / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / "order_analytics.csv"
result.to_csv(output_path, index=False)

print("\nSaved to:", output_path)