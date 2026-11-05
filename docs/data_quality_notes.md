# Data Quality Notes

## Customers

### Grain
One row represents one customer record associated with an order.

### Key Findings
- 99,441 customer records
- 99,441 unique `customer_id` values
- 96,096 unique `customer_unique_id` values
- No missing `customer_id` values
- No missing `customer_unique_id` values
- No exact duplicate rows

### Interpretation
`customer_id` (Primary Key) uniquely identifies each customer record and is treated as the primary key candidate.

`customer_unique_id` represents the persistent customer identity. A single real customer may therefore be associated with multiple customer records and orders.

---

## Orders

## Order Items Profiling

### Structure and keys
- Grain: one order-item record per row.
- Rows: 112,650.
- Distinct orders: 98,666.
- No missing values or fully duplicated rows.
- (order_id, order_item_id) is unique and non-null.
- All order_id values exist in Orders.
- Product and seller foreign keys have not yet been checked.

### Orders without items
775 orders have no matching item records:
- unavailable: 603
- canceled: 164
- created: 5
- invoiced: 2
- shipped: 1

Keep these orders and flag them with has_items = False.
Their missing item amounts remain null.
Statuses suggest possible explanations but do not establish causes.
Prioritize investigation of invoiced and shipped orders without items.

### Numeric checks
- Prices are positive; range: 0.85–6,735.00.
- Freight values are non-negative; range: 0–409.68.
- 383 item records have zero freight; retained pending clarification.
- High values are retained pending further investigation.

### Aggregation and join validation
Items were aggregated by order_id before a left join to Orders.
- Result: 99,441 rows and 99,441 unique orders.
- Join validation: one_to_one passed.
- Item price total before and after: 13,591,643.70.
- Freight total before and after: 2,251,909.54.
- Item totals represent recorded merchandise amounts, not confirmed revenue.

### Grain
One row represents one order.

### Key Findings
- 99,441 order records
- 99,441 unique `order_id` values
- No missing `order_id` values
- No exact duplicate rows
- All `customer_id` foreign keys match records in the customers table

### Missing Values
- `order_approved_at`: 160
- `order_delivered_carrier_date`: 1,783
- `order_delivered_customer_date`: 2,965

### Business Interpretation
Missing delivery timestamps are not automatically data-quality errors.

Most missing `order_delivered_customer_date` values occur for orders that have not reached the delivered state, including shipped, canceled, unavailable, processing, invoiced, approved, and created orders.

Eight orders marked as `delivered` have a missing customer delivery timestamp and should be flagged for investigation.

### Initial Data Quality Rule

**DQ-ORD-001**

If `order_status == "delivered"`, then `order_delivered_customer_date` should not be null.

Observed violations: 8.

Treatment: Flag for investigation rather than automatically dropping or imputing the records.


## Payments Profiling and Reconciliation

### Structure and keys
- Grain: one payment record within an order.
- Rows: 103,886; distinct orders: 99,440.
- No missing values or fully duplicated rows.
- (order_id, payment_sequential) is unique and non-null.
- All payment order_id values exist in Orders.
- payment_value is not multiplied by payment_installments.

### Special records
- No negative payment values.
- 9 zero-value records across 8 orders:
  - 6 voucher records across 5 orders with positive payment totals.
  - 3 not_defined records across 3 canceled orders with zero totals.
- 2 credit-card records have zero installments and positive amounts.
- 1 delivered order has no payment record:
  bfbd0f9bdef84302105ad712db648a6c
- Retain original values and flag these cases.
- Missing payment amounts remain null.

### Aggregation validation
- Payments aggregated by order_id before joining to Orders.
- Result: 99,441 rows and unique orders.
- Payment total before and after: 16,008,872.12.

### Order-level reconciliation
Difference = payment_total - (items_total + freight_total).
Comparison uses rounded integer cents with a 1-cent tolerance.

- Comparable orders: 98,665.
- Within tolerance: 98,362.
- Not comparable: 776
  - 775 without item records.
  - 1 without payment records.
- Mismatches: 303
  - Payment higher: 264; payment lower: 39.
  - Absolute difference:
    - 2–5 cents: 43
    - 6–100 cents: 11
    - 101–1,000 cents: 151
    - Above 1,000 cents: 98
  - Statuses: delivered 299, canceled 2, shipped 2.

### Decisions and limitations
- Retain mismatches and original monetary values.
- Do not increase tolerance merely to improve the match rate.
- Raw records support the three largest observed differences.
- All three use credit-card installments; the cause remains unconfirmed.
- Recorded payments are not sufficient to establish net revenue
  or confirm refunds and settlement.


  ## Products Profiling

### Structure and keys
- Grain: one product per row.
- Rows and distinct product IDs: 32,951.
- No missing or duplicate product IDs; no fully duplicated rows.
- All Order Items product IDs exist in Products.
- Product join passed many_to_one validation.
- Joined item row count remains 112,650.
- 73 distinct non-null product categories.

### Missing attributes and impact
- 610 products jointly lack category, name length,
  description length, and photo count.
- Missing categories affect 1,603 item records across 1,451 orders.
- 2 products jointly lack weight and all three dimensions,
  affecting 18 item records.
- 4 products have zero weight, affecting 8 item records.
- No negative weights or non-positive recorded dimensions.
- Overlap between issue groups has not been checked.

### Handling decisions
- Retain all products and original attribute values.
- Add explicit quality flags.
- Use unknown in a separate reporting-category field
  while preserving the original null category.
- Do not replace missing physical measurements with zero.
- Zero weights remain flagged for investigation.
- Existing fields contain name/description lengths, not their text.