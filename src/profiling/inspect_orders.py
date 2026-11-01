import pandas as pd

'''
loading the orders dataset and customers dataset for inspection
'''
order_path = "data/raw/olist_orders_dataset.csv"
orders = pd.read_csv(order_path)
customers_path = "data/raw/olist_customers_dataset.csv"
customers = pd.read_csv(customers_path)

'''
Inspecting the orders dataset
show data shape, columns, data types, info
and validation of order_id and customer_id,
duplicate rows, missing values
'''

print("\n--- SHAPE ---")
print(orders.shape)

print("\n--- COLUMNS ---")
print(orders.columns)

print("\n--- DATA TYPES ---")
print(orders.dtypes)

print("\n--- INFO ---")
orders.info()

print("\n--- Order_ID VALIDATION ---")
print("Total rows:", len(orders))
print("Unique order_id:", orders["order_id"].nunique())
print("Missing order_id:", orders["order_id"].isna().sum())

print("\n--- CUSTOMER_ID VALIDATION ---")
print("Unique customer_id:", orders["customer_id"].nunique())
print("Missing customer_id:",orders["customer_id"].isna().sum())

print("\n--- DUPLICATE ROWS ---")
print(orders.duplicated().sum())

print("\n--- MISSING VALUES ---")
print(orders.isna().sum())

'show foreign key validation for customer_id'
customer_fk_exists = orders["customer_id"].isin(
    customers["customer_id"]
)
print("\n--- CUSTOMER FOREIGN KEY VALIDATION ---")
print(customer_fk_exists.value_counts())

'check for invalid customer foreign keys in the orders dataset'
invalid_customer_fk = (~customer_fk_exists).sum()
print("Invalid customer foreign keys:", invalid_customer_fk)

'show order status counts in the orders dataset'
print("\n--- ORDER STATUS COUNTS ---")
print(orders["order_status"].value_counts())

'check for missing delivery dates in the orders dataset'
'add column (delivery_date_missing) to indicate if delivery date is missing'
orders["delivery_date_missing"] = (
    orders["order_delivered_customer_date"].isna()
)

'show missing delivery dates by order status in the orders dataset'
missing_by_status = (
    orders.groupby("order_status")["delivery_date_missing"]
    .agg(["count", "sum", "mean"])
)

missing_by_status["missing_pct"] = (
    missing_by_status["mean"] * 100
)
print("\n--- DELIVERY DATE MISSING BY STATUS ---")
print(missing_by_status)


delivered_missing_date = orders[
    (orders["order_status"] == "delivered")
    & (orders["order_delivered_customer_date"].isna())
]

print("\n--- DELIVERED ORDERS WITH MISSING DELIVERY DATE ---")
print("Count:", len(delivered_missing_date))

print("\n--- DELIVERED ORDERS WITH MISSING DELIVERY DATE ---")
print(
    delivered_missing_date[
        [
            "order_id",
            "customer_id",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ]
)