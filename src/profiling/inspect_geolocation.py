from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

geo = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_geolocation_dataset.csv",
    dtype={"geolocation_zip_code_prefix": "string"},
)

print("First 5 rows:")
print(geo.head().to_string(index=False))

print("\nRows =", len(geo))
print("Columns =", geo.shape[1])

print("\nMissing values by column:")
print(geo.isna().sum())

print("\nUnique ZIP prefixes =",
      geo["geolocation_zip_code_prefix"].nunique())

print("Duplicate ZIP prefix occurrences =",
      geo["geolocation_zip_code_prefix"].duplicated().sum())

print("Duplicate entire rows =", geo.duplicated().sum())

# extract zip prefix and check if it is a valid 5-digit number
valid_zip = (
    geo["geolocation_zip_code_prefix"]
    .str.fullmatch(r"\d{5}")
    .fillna(False)
)
print("\nMissing or malformed ZIP prefixes =", (~valid_zip).sum())

print("\nCoordinate summary:")
print(geo[["geolocation_lat", "geolocation_lng"]].describe())

# check for valid coordinate ranges
valid_coordinates = (
    geo["geolocation_lat"].between(-90, 90)
    & geo["geolocation_lng"].between(-180, 180)
)
print("\nMissing or out-of-range coordinate rows =",
      (~valid_coordinates).sum())

# check if a prefix corresponds to different cities or states
prefix_summary = (
    geo.groupby("geolocation_zip_code_prefix")
    .agg(
        record_count=("geolocation_lat", "size"),
        city_count=("geolocation_city", "nunique"),
        state_count=("geolocation_state", "nunique"),
    )
)

print("\nRecords per ZIP prefix:")
print(prefix_summary["record_count"].describe())

print("\nZIP prefixes with multiple city names =",
      prefix_summary["city_count"].gt(1).sum())

print("ZIP prefixes with multiple states =",
      prefix_summary["state_count"].gt(1).sum())


# part 2
# keep geo records withn unique zip
geo_unique = geo.drop_duplicates().copy()

print("\nRows after exact deduplication =", len(geo_unique))
print("ZIP prefixes retained =",
      geo_unique["geolocation_zip_code_prefix"].nunique())

# check multi-state ZIP prefixes
multi_state_prefixes = prefix_summary.index[
    prefix_summary["state_count"].gt(1)
]

print("\nMulti-state ZIP prefixes:")
print(
    geo_unique.loc[
        geo_unique["geolocation_zip_code_prefix"].isin(
            multi_state_prefixes
        )
    ]
    .groupby(
        ["geolocation_zip_code_prefix", "geolocation_state"]
    )
    .size()
    .rename("unique_record_count")
    .to_string()
)

# check coordinate extremes
extreme_indices = [
    geo_unique["geolocation_lat"].idxmin(),
    geo_unique["geolocation_lat"].idxmax(),
    geo_unique["geolocation_lng"].idxmin(),
    geo_unique["geolocation_lng"].idxmax(),
]

print("\nCoordinate extremes:")
print(
    geo_unique.loc[extreme_indices]
    .drop_duplicates()
    .to_string(index=False)
)

# check first 3 ZIP prefixes that correspond to multiple cities
multi_city_prefixes = prefix_summary.index[
    prefix_summary["city_count"].gt(1)
][:3]

print("\nSample city-name variations:")
print(
    geo_unique.loc[
        geo_unique["geolocation_zip_code_prefix"].isin(
            multi_city_prefixes
        ),
        [
            "geolocation_zip_code_prefix",
            "geolocation_city",
            "geolocation_state",
        ],
    ]
    .drop_duplicates()
    .sort_values(
        ["geolocation_zip_code_prefix", "geolocation_city"]
    )
    .to_string(index=False)
)



# part 3
import unicodedata

def normalize_city(value):
    # normalization: remove accents, convert to lowercase, and trim whitespace
    text = unicodedata.normalize("NFKD", value)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return " ".join(text.casefold().split())


# new field, keeping the original city name
geo_unique["city_normalized"] = (
    geo_unique["geolocation_city"].map(normalize_city)
)

# one row per zip prefix, recording only the confirmed information
geo_prefix_quality = (
    geo_unique.groupby(
        "geolocation_zip_code_prefix",
        as_index=False,
    )
    .agg(
        unique_record_count=("geolocation_lat", "size"),
        city_count_raw=("geolocation_city", "nunique"),
        city_count_normalized=("city_normalized", "nunique"),
        state_count=("geolocation_state", "nunique"),
    )
)

geo_prefix_quality["has_city_ambiguity"] = (
    geo_prefix_quality["city_count_normalized"].gt(1)
)
geo_prefix_quality["has_state_conflict"] = (
    geo_prefix_quality["state_count"].gt(1)
)

print("\nPrefix summary rows =", len(geo_prefix_quality))
print("Duplicate prefix keys =",
      geo_prefix_quality[
          "geolocation_zip_code_prefix"
      ].duplicated().sum())

print("\nPrefixes with multiple raw city names =",
      geo_prefix_quality["city_count_raw"].gt(1).sum())

print("Prefixes with multiple normalized city names =",
      geo_prefix_quality["has_city_ambiguity"].sum())

print("Prefixes resolved by city-name normalization =",
      (
          geo_prefix_quality["city_count_raw"].gt(1)
          & geo_prefix_quality["city_count_normalized"].eq(1)
      ).sum())

print("Prefixes with state conflicts =",
      geo_prefix_quality["has_state_conflict"].sum())



# part 4
customers = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_customers_dataset.csv",
    dtype={
        "customer_id": "string",
        "customer_zip_code_prefix": "string",
    },
)

sellers = pd.read_csv(
    PROJECT_ROOT / "data" / "raw" / "olist_sellers_dataset.csv",
    dtype={
        "seller_id": "string",
        "seller_zip_code_prefix": "string",
    },
)

for label, source, zip_col in [
    ("Customers", customers, "customer_zip_code_prefix"),
    ("Sellers", sellers, "seller_zip_code_prefix"),
]:
    # check formate of ZIP prefix
    valid_zip = (
        source[zip_col]
        .str.fullmatch(r"[0-9]{5}")
        .fillna(False)
    )

    checked = source.merge(
        geo_prefix_quality,
        left_on=zip_col,
        right_on="geolocation_zip_code_prefix",
        how="left",
        validate="many_to_one",
        indicator="geo_match",
    )

    matched = checked["geo_match"].eq("both")

    print(f"\n{label}:")
    print("Source rows =", len(source))
    print("Rows after join =", len(checked))
    print("Missing or malformed ZIP prefixes =", (~valid_zip).sum())

    print("Rows with matching geo prefix =", matched.sum())
    print("Rows without matching geo prefix =", (~matched).sum())
    print(
        "Distinct unmatched ZIP prefixes =",
        checked.loc[~matched, zip_col].nunique(),
    )

    print(
        "Rows linked to city ambiguity =",
        checked.loc[matched, "has_city_ambiguity"].sum(),
    )
    print(
        "Rows linked to state conflict =",
        checked.loc[matched, "has_state_conflict"].sum(),
    )

    print("Sample unmatched ZIP prefixes:")
    print(
        checked.loc[~matched, zip_col]
        .value_counts()
        .head(10)
        .to_string()
    )