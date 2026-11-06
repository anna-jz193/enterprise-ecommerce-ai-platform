# Enterprise E-Commerce Data & AI Platform

## Overview

This project builds an AWS-based enterprise data and AI platform using e-commerce operational data and enterprise knowledge documents.

The final system will integrate:

- cloud data ingestion and validation
- analytics-ready structured data
- enterprise knowledge retrieval using RAG
- natural-language access to business data
- LLM evaluation, security, and monitoring

## Dataset

Brazilian E-Commerce Public Dataset by Olist.

## Current Status

Phase 1 - Data Understanding and Profiling

Completed:
- Set up the Python development environment
- Loaded and inspected the Olist customer and order datasets
- Validated candidate primary and foreign keys
- Checked duplicate and missing-value patterns
- Validated referential integrity between customers and orders
- Investigated order delivery-date missingness by order status
- Identified initial business-aware data quality rules

In Progress:
- Profiling order items, products, and sellers
- Building the project data dictionary
- Designing the initial entity-relationship diagram (ERD)


## Data Transformations

### Product dimension

Run from the project root:

```bash
python src/transforms/build_products.py
```

Output: `data/processed/dim_products.csv`

- Grain: one row per product_id.
- Preserves original attributes and adds data quality flags.
- Reporting category fallback: English -> original category -> unknown.
- Validates product keys, translation keys, and output row count.
- Re-running replaces the generated file; raw inputs remain unchanged.
- Generated data is excluded from Git.



### Order analytics

Run from the project root:

```bash
python src/transforms/build_orders.py
```

Output: `data/processed/order_analytics.csv`

- Grain: one row per order_id.
- Aggregates items, payments, and reviews separately before joining.
- Preserves all orders through validated one-to-one left joins.
- Includes item and seller counts, merchandise and freight totals,
  payment summaries, review summaries, and quality flags.
- Reconciliation uses integer cents with a 1-cent tolerance.
- Missing source records remain distinguishable from zero amounts.
- Review mean is a project-defined summary.
- Recorded monetary amounts are not confirmed net revenue.
- Re-running replaces the generated file; raw inputs remain unchanged.

## Current Technology Stack

- Python
- Pandas
- Git
- GitHub

## Planned Technology Stack

- SQL
- AWS
- Amazon Bedrock

