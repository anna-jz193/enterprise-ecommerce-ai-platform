import pandas as pd


file_path = "data/raw/olist_customers_dataset.csv"
customers = pd.read_csv(file_path)

'show data shape, columns, data types, info'
print("\n--- SHAPE ---")
print(customers.shape)

print("\n--- COLUMNS ---")
print(customers.columns)

print("\n--- DATA TYPES ---")
print(customers.dtypes)

print("\n--- INFO ---")
customers.info()

'check for customer_unique_id validation - duplicate rows, missing values'
print("\n--- CUSTOMER_ID VALIDATION ---")
print("Total rows:", len(customers))
print("Unique customer_id:", customers["customer_id"].nunique())
print("Missing customer_id:", customers["customer_id"].isna().sum())

print("\n--- CUSTOMER_UNIQUE_ID VALIDATION ---")
print(
    "Unique customer_unique_id:",
    customers["customer_unique_id"].nunique()
)
print(
    "Missing customer_unique_id:",
    customers["customer_unique_id"].isna().sum()
)

print("\n--- DUPLICATE ROWS ---")
print(customers.duplicated().sum())

print("\n--- MISSING VALUES ---")
print(customers.isna().sum())

print("\n--- CUSTOMER STATES ---")
print(customers["customer_state"].value_counts())