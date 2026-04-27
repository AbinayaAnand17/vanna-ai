-- Sonline AI Demo Database Initialization Script
-- This script sets up sample data for the Sonline AI dashboard

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

-- Create customers_summary view (for training examples)
CREATE OR REPLACE VIEW customers_summary AS
SELECT 
    u.user_id,
    u.name,
    u.email,
    COUNT(o.order_id) as total_orders,
    COALESCE(SUM(o.total_amount), 0) as total_spent,
    MAX(o.order_date) as last_order_date
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.name, u.email;

-- Insert sample users
INSERT INTO users (name, email, phone, country) VALUES
    ('Alice Johnson', 'alice.johnson@example.com', '+1-555-0101', 'USA'),
    ('Bob Smith', 'bob.smith@example.com', '+1-555-0102', 'USA'),
    ('Carol Williams', 'carol.williams@example.com', '+1-555-0103', 'Canada'),
    ('David Brown', 'david.brown@example.com', '+1-555-0104', 'USA'),
    ('Eva Martinez', 'eva.martinez@example.com', '+34-91-555-0105', 'Spain'),
    ('Frank Miller', 'frank.miller@example.com', '+1-555-0106', 'USA'),
    ('Grace Lee', 'grace.lee@example.com', '+65-6555-0107', 'Singapore'),
    ('Henry Garcia', 'henry.garcia@example.com', '+1-555-0108', 'USA'),
    ('Iris Chen', 'iris.chen@example.com', '+886-2-555-0109', 'Taiwan'),
    ('Jack Wilson', 'jack.wilson@example.com', '+1-555-0110', 'USA');

-- Insert sample products
INSERT INTO products (name, category, price, stock_quantity, description) VALUES
    ('Laptop Pro 15"', 'Electronics', 1499.99, 45, 'High-performance laptop for professionals'),
    ('Wireless Mouse', 'Electronics', 49.99, 200, 'Ergonomic wireless mouse with precision tracking'),
    ('USB-C Hub', 'Electronics', 79.99, 150, '7-in-1 USB-C hub with multiple ports'),
    ('Mechanical Keyboard', 'Electronics', 129.99, 80, 'RGB mechanical keyboard with custom switches'),
    ('Monitor 4K 27"', 'Electronics', 399.99, 30, '4K IPS monitor for professional work'),
    ('Desk Lamp LED', 'Furniture', 59.99, 120, 'Adjustable LED desk lamp with USB charging'),
    ('Standing Desk', 'Furniture', 299.99, 25, 'Electric standing desk with memory presets'),
    ('Office Chair', 'Furniture', 249.99, 35, 'Ergonomic office chair with lumbar support'),
    ('Desk Organizer', 'Accessories', 24.99, 200, 'Bamboo desk organizer with multiple compartments'),
    ('Cable Management', 'Accessories', 19.99, 300, 'Cable clips and management sleeves combo pack');

-- Insert sample orders
INSERT INTO orders (user_id, order_date, total_amount, status, shipping_address) VALUES
    (1, '2024-01-15 10:30:00', 1649.97, 'completed', '123 Main St, New York, NY'),
    (2, '2024-01-18 14:45:00', 899.98, 'completed', '456 Oak Ave, Boston, MA'),
    (3, '2024-01-20 09:15:00', 2199.97, 'completed', '789 Maple Rd, Toronto, ON'),
    (4, '2024-02-05 11:20:00', 599.98, 'pending', '321 Elm St, Chicago, IL'),
    (5, '2024-02-08 16:30:00', 379.99, 'completed', 'Calle Principal 123, Madrid, Spain'),
    (1, '2024-02-10 13:00:00', 129.99, 'completed', '123 Main St, New York, NY'),
    (6, '2024-02-15 08:45:00', 1799.97, 'processing', '654 Pine Ave, Los Angeles, CA'),
    (7, '2024-02-18 15:20:00', 449.98, 'pending', 'Orchard Road, Singapore'),
    (2, '2024-02-20 10:30:00', 249.99, 'completed', '456 Oak Ave, Boston, MA'),
    (8, '2024-02-22 12:15:00', 1949.95, 'processing', '987 Birch Ln, Houston, TX'),
    (4, '2024-02-25 14:40:00', 679.97, 'completed', '321 Elm St, Chicago, IL'),
    (9, '2024-03-01 09:30:00', 299.98, 'pending', 'Taipei 101 District, Taipei'),
    (3, '2024-03-05 16:00:00', 839.99, 'completed', '789 Maple Rd, Toronto, ON'),
    (5, '2024-03-08 11:45:00', 529.98, 'completed', 'Calle Principal 123, Madrid, Spain'),
    (10, '2024-03-10 13:20:00', 1399.97, 'processing', '159 Cedar Way, Phoenix, AZ');

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
    (1, 1, 1, 1499.99, 1499.99),
    (1, 2, 1, 49.99, 49.99),
    (1, 9, 2, 24.99, 49.98),
    (2, 4, 1, 129.99, 129.99),
    (2, 6, 1, 59.99, 59.99),
    (2, 10, 1, 19.99, 19.99),
    (2, 2, 1, 49.99, 49.99),
    (2, 9, 5, 24.99, 124.95),
    (2, 10, 1, 19.99, 19.99),
    (3, 5, 1, 399.99, 399.99),
    (3, 8, 1, 249.99, 249.99),
    (3, 7, 1, 299.99, 299.99),
    (3, 6, 1, 59.99, 59.99),
    (3, 9, 4, 24.99, 99.96),
    (3, 10, 2, 19.99, 39.98),
    (4, 1, 1, 1499.99, 1499.99),
    (4, 10, 1, 19.99, 19.99),
    (5, 6, 1, 59.99, 59.99),
    (5, 2, 1, 49.99, 49.99),
    (5, 9, 4, 24.99, 99.96),
    (5, 10, 2, 19.99, 39.99),
    (6, 4, 1, 129.99, 129.99),
    (7, 1, 1, 1499.99, 1499.99),
    (7, 3, 1, 79.99, 79.99),
    (7, 10, 2, 19.99, 39.99),
    (8, 6, 1, 59.99, 59.99),
    (8, 9, 3, 24.99, 74.97),
    (8, 2, 1, 49.99, 49.99),
    (8, 10, 3, 19.99, 59.97),
    (9, 8, 1, 249.99, 249.99),
    (10, 1, 1, 1499.99, 1499.99),
    (10, 2, 1, 49.99, 49.99),
    (10, 9, 2, 24.99, 49.98),
    (11, 5, 1, 399.99, 399.99),
    (11, 6, 1, 59.99, 59.99),
    (11, 10, 1, 19.99, 19.99),
    (12, 4, 1, 129.99, 129.99),
    (12, 2, 1, 49.99, 49.99),
    (12, 9, 2, 24.99, 49.98),
    (13, 3, 1, 79.99, 79.99),
    (13, 6, 1, 59.99, 59.99),
    (13, 9, 4, 24.99, 99.96),
    (13, 10, 2, 19.99, 39.99),
    (13, 2, 1, 49.99, 49.99),
    (13, 8, 1, 249.99, 249.99),
    (14, 5, 1, 399.99, 399.99),
    (14, 9, 3, 24.99, 74.97),
    (14, 10, 2, 19.99, 39.99),
    (14, 2, 1, 49.99, 49.99),
    (15, 1, 1, 1499.99, 1499.99),
    (15, 4, 1, 129.99, 129.99),
    (15, 6, 1, 59.99, 59.99),
    (15, 9, 3, 24.99, 74.97);

-- Create indexes for better performance
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_products_category ON products(category);

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Display completion message
SELECT 'Database initialization completed successfully!' as status;

