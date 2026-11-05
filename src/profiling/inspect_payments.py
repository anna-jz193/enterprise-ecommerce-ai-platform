from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

payments = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_order_payments_dataset.csv",
    dtype={
        "order_id": "string",
        "payment_sequential": "Int64",
        "payment_installments": "Int64",
    },
)

print("First 5 rows:")
print(payments.head().to_string(index=False))

print("\nRows =", len(payments))
print("Columns =", payments.shape[1])
print("Unique orders =", payments["order_id"].nunique())

print("\nDuplicate order/payment pairs =",
      payments.duplicated(
          subset=["order_id", "payment_sequential"]
      ).sum())

print("Duplicate entire rows =", payments.duplicated().sum())

print("\nMissing values by column:")
print(payments.isna().sum())

print("\nPayment types:")
print(payments["payment_type"].value_counts(dropna=False))

print("\nPayment amount and installments summary:")
print(payments[["payment_value", "payment_installments"]].describe())



orders = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_orders_dataset.csv",
    dtype={"order_id": "string"},
)

# 1. match payments to orders
invalid_payments = payments.loc[
    ~payments["order_id"].isin(orders["order_id"])
]

print("\nPayment rows with invalid order foreign keys =",
      len(invalid_payments))

# 2. show orders that do not have any payments
orders_without_payments = orders.loc[
    ~orders["order_id"].isin(payments["order_id"])
]

print("\nOrders without payments =", len(orders_without_payments))
print(
    orders_without_payments[
        ["order_id", "order_status", "order_purchase_timestamp"]
    ].to_string(index=False)
)

# 3. check for negative payment values, zero payment values, zero installments, and non-positive payment sequence numbers
print("\nNegative payment values =",
      (payments["payment_value"] < 0).sum())
print("Zero payment values =",
      (payments["payment_value"] == 0).sum())
print("Zero installments =",
      (payments["payment_installments"] == 0).sum())
print("Non-positive payment sequence numbers =",
      (payments["payment_sequential"] <= 0).sum())

# 4. show special records
special_payments = payments.loc[
    (payments["payment_value"] == 0)
    | (payments["payment_installments"] == 0)
    | (payments["payment_type"] == "not_defined")
]

special_details = special_payments.merge(
    orders[["order_id", "order_status"]],
    on="order_id",
    how="left",
    validate="many_to_one",
)

print("\nSpecial payment records:")
print(special_details.to_string(index=False))


# 5. create flags for special payment records and aggregate by order_id
payments["is_zero_payment"] = payments["payment_value"].eq(0)
payments["is_undefined_type"] = payments["payment_type"].eq("not_defined")
payments["is_zero_installments"] = payments["payment_installments"].eq(0)

# 6. row per column aggregation for each order_id
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

# 7. keep all orders, even those without payments, and merge with the payment_summary
order_payment_summary = orders.merge(
    payment_summary,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator=True,
)

order_payment_summary["has_payment_record"] = (
    order_payment_summary["_merge"].eq("both")
)
order_payment_summary = order_payment_summary.drop(columns="_merge")

print("\nRows after merge =", len(order_payment_summary))
print("Unique orders after merge =",
      order_payment_summary["order_id"].nunique())

print("\nHas payment record:")
print(order_payment_summary["has_payment_record"].value_counts())

print("\nPayment total before aggregation =",
      round(payments["payment_value"].sum(), 2))
print("Payment total after merge =",
      round(order_payment_summary["payment_total"].sum(min_count=1), 2))

# 8. show orders that have zero-value payment records
zero_payment_orders = payment_summary.loc[
    payment_summary["has_zero_payment"],
    ["order_id", "payment_record_count", "payment_total"],
]

print("\nOrders containing zero-value payment records:")
print(zero_payment_orders.to_string(index=False))



items = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_order_items_dataset.csv",
    dtype={"order_id": "string"},
)

# 1. aggregate item totals by order_id
item_totals = (
    items.groupby("order_id", as_index=False)
    .agg(
        items_total=("price", "sum"),
        freight_total=("freight_value", "sum"),
    )
)

reconciliation = order_payment_summary.merge(
    item_totals,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator="item_match",
)

reconciliation["has_items"] = reconciliation["item_match"].eq("both")

 
comparable = (
    reconciliation["has_payment_record"]
    & reconciliation["has_items"]
)

# convert payment_total, items_total, and freight_total to cents for comparison
payment_cents = (
    reconciliation["payment_total"].mul(100).round().astype("Int64")
)
item_cents = (
    reconciliation["items_total"].mul(100).round().astype("Int64")
)
freight_cents = (
    reconciliation["freight_total"].mul(100).round().astype("Int64")
)

reconciliation["difference_cents"] = (
    payment_cents - item_cents - freight_cents
)

# create a new column to indicate whether the payment total matches the sum of item total and freight total
reconciliation["amount_check"] = "not_comparable"

reconciliation.loc[comparable, "amount_check"] = "within_tolerance"

mismatch = (
    comparable
    & reconciliation["difference_cents"].abs().gt(1).fillna(False)
)

reconciliation.loc[mismatch, "amount_check"] = "mismatch"

print("\nReconciliation rows =", len(reconciliation))

print("\nRecord coverage:")
print(pd.crosstab(
    reconciliation["has_items"],
    reconciliation["has_payment_record"],
))

print("\nAmount check:")
print(reconciliation["amount_check"].value_counts())

print("\nFirst 10 mismatched orders:")
print(
    reconciliation.loc[
        mismatch,
        [
            "order_id",
            "order_status",
            "items_total",
            "freight_total",
            "payment_total",
            "difference_cents",
        ],
    ].head(10).to_string(index=False)
)


mismatches = reconciliation.loc[mismatch].copy()

mismatches["abs_difference_cents"] = (
    mismatches["difference_cents"].abs()
)

print("\nMismatch direction:")
print("Payment higher =",
      (mismatches["difference_cents"] > 0).sum())
print("Payment lower =",
      (mismatches["difference_cents"] < 0).sum())

print("\nMismatch size:")
print(
    pd.cut(
        mismatches["abs_difference_cents"],
        bins=[1, 5, 100, 1000, float("inf")],
        labels=[
            "2–5 cents",
            "6–100 cents",
            "101–1000 cents",
            "Above 1000 cents",
        ],
    ).value_counts(sort=False)
)

print("\nMismatch order statuses:")
print(mismatches["order_status"].value_counts())

# find the first 3 mismatches by absolute difference in cents
largest = mismatches.nlargest(3, "abs_difference_cents")

print("\nLargest 3 mismatches:")
print(
    largest[
        [
            "order_id",
            "order_status",
            "items_total",
            "freight_total",
            "payment_total",
            "difference_cents",
        ]
    ].to_string(index=False)
)

for order_id in largest["order_id"]:
    print(f"\nOrder: {order_id}")

    print("Item records:")
    print(
        items.loc[
            items["order_id"].eq(order_id),
            ["order_item_id", "price", "freight_value"],
        ].to_string(index=False)
    )

    print("Payment records:")
    print(
        payments.loc[
            payments["order_id"].eq(order_id),
            [
                "payment_sequential",
                "payment_type",
                "payment_installments",
                "payment_value",
            ],
        ].to_string(index=False)
    )