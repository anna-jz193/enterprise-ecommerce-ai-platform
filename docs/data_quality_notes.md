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
`customer_id` uniquely identifies each customer record and is treated as the primary key candidate.

`customer_unique_id` represents the persistent customer identity. A single real customer may therefore be associated with multiple customer records and orders.

---

## Orders

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