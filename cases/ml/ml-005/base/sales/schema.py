"""Table schemas.

orders:            one row per order - order_id (unique), customer_id, amount_cents, created_at
customer_segments: one row per customer per month - customer_id, month ("YYYY-MM"), segment
                   (a customer's segment can change from month to month)
"""
