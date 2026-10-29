CREATE TABLE customers (
  id bigint PRIMARY KEY,
  email text NOT NULL,
  name text NOT NULL
);

CREATE TABLE orders (
  id bigint PRIMARY KEY,
  order_key text NOT NULL UNIQUE,
  customer_id bigint NOT NULL REFERENCES customers (id),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'shipped', 'cancelled')),
  sales_rep_name text NOT NULL
);

COMMENT ON TABLE customers IS 'People and companies that place orders.';
COMMENT ON COLUMN customers.id IS 'Surrogate key.';
COMMENT ON COLUMN customers.email IS 'Contact email. PII.';
COMMENT ON COLUMN customers.name IS 'Contact name. PII.';
COMMENT ON TABLE orders IS 'One row per imported order.';
COMMENT ON COLUMN orders.id IS 'Surrogate key.';
COMMENT ON COLUMN orders.order_key IS 'Natural key from the warehouse file; unique.';
COMMENT ON COLUMN orders.customer_id IS 'The customer who placed the order.';
COMMENT ON COLUMN orders.status IS 'open, shipped or cancelled.';
COMMENT ON COLUMN orders.sales_rep_name IS 'The rep who owns the order; drives the row rule for reps.';
