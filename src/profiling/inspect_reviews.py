from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

reviews = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_order_reviews_dataset.csv",
    dtype={
        "review_id": "string",
        "order_id": "string",
    },
)

orders = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_orders_dataset.csv",
    dtype={"order_id": "string"},
)

print("First 5 rows:")
print(reviews.head().to_string(index=False))

print("\nRows =", len(reviews))
print("Columns =", reviews.shape[1])

print("\nUnique review_id =", reviews["review_id"].nunique())
print("Unique order_id =", reviews["order_id"].nunique())

print("\nDuplicate review_id =",
      reviews["review_id"].duplicated().sum())
print("Duplicate review/order pairs =",
      reviews.duplicated(subset=["review_id", "order_id"]).sum())
print("Duplicate entire rows =", reviews.duplicated().sum())

print("\nMissing values by column:")
print(reviews.isna().sum())

print("\nReview score distribution:")
print(reviews["review_score"].value_counts(dropna=False).sort_index())

invalid_scores = (
    reviews["review_score"].isna()
    | ~reviews["review_score"].isin([1, 2, 3, 4, 5])
)
print("Missing or invalid review scores =", invalid_scores.sum())

# exisitness check: review_id and order_id should exist in reviews and orders respectively
invalid_review_orders = reviews.loc[
    ~reviews["order_id"].isin(orders["order_id"])
]
print("\nReview rows with invalid order foreign keys =",
      len(invalid_review_orders))

# existence check: which orders have no review records?
orders_without_reviews = orders.loc[
    ~orders["order_id"].isin(reviews["order_id"])
]
print("Orders without reviews =", len(orders_without_reviews))

# check if an order has multiple review records
reviews_per_order = reviews.groupby("order_id").size()

print("\nOrders with multiple review records =",
      reviews_per_order.gt(1).sum())
print("Maximum review records per order =", reviews_per_order.max())



# new copy of original date info. 
date_cols = [
    "review_creation_date",
    "review_answer_timestamp",
]

for col in date_cols:
    parsed_col = f"{col}_parsed"

    reviews[parsed_col] = pd.to_datetime(
        reviews[col],
        errors="coerce",
    )

    parse_failed = (
        reviews[col].notna()
        & reviews[parsed_col].isna()
    )

    print(f"\nFailed to parse {col} =", parse_failed.sum())

# check for timestamp order: review_answer_timestamp should be after review_creation_date
valid_dates = (
    reviews["review_creation_date_parsed"].notna()
    & reviews["review_answer_timestamp_parsed"].notna()
)

answer_before_creation = (
    valid_dates
    & (
        reviews["review_answer_timestamp_parsed"]
        < reviews["review_creation_date_parsed"]
    )
)

print("\nAnswers before review creation =",
      answer_before_creation.sum())

# check for empty comments: treat empty strings and whitespace as no comment
reviews["has_comment_title"] = (
    reviews["review_comment_title"]
    .astype("string")
    .fillna("")
    .str.strip()
    .ne("")
)

reviews["has_comment_message"] = (
    reviews["review_comment_message"]
    .astype("string")
    .fillna("")
    .str.strip()
    .ne("")
)

print("\nReviews with title =", reviews["has_comment_title"].sum())
print("Reviews with message =", reviews["has_comment_message"].sum())

# check for orders with multiple reviews
multiple_review_orders = reviews_per_order.loc[
    reviews_per_order.gt(1)
].head(3).index

print("\nSample orders with multiple reviews:")

sample_reviews = (
    reviews.loc[
        reviews["order_id"].isin(multiple_review_orders)
    ]
    .sort_values(["order_id", "review_answer_timestamp_parsed"])
)

print(
    sample_reviews[
        [
            "order_id",
            "review_id",
            "review_score",
            "review_creation_date",
            "review_answer_timestamp",
        ]
    ].to_string(index=False)
)



# row per order summary of reviews
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

# keep all orders
order_review_summary = orders.merge(
    review_summary,
    on="order_id",
    how="left",
    validate="one_to_one",
    indicator="review_match",
)

order_review_summary["has_review_record"] = (
    order_review_summary["review_match"].eq("both")
)
order_review_summary = order_review_summary.drop(columns="review_match")

print("\nRows after review merge =", len(order_review_summary))
print("Unique orders after review merge =",
      order_review_summary["order_id"].nunique())

print("\nHas review record:")
print(order_review_summary["has_review_record"].value_counts())

print("\nReview count preserved =",
      review_summary["review_count"].sum() == len(reviews))

print("Orders with differing review scores =",
      review_summary["has_score_disagreement"].sum())

# check for orders with no review message
print("\nReviewed orders without any message =",
      (~review_summary["has_review_message"]).sum())