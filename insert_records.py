import sqlite3
import random
from faker import Faker

# Initialize Faker
fake = Faker()

# Connect to SQLite database
db_name = "nvidia_sales.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()


# Recreate Tables with Foreign Keys
cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone_number TEXT UNIQUE NOT NULL,
        region TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Sales_Region (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Sales_Team (
        sales_rep_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        region_id INTEGER NOT NULL,
        FOREIGN KEY (region_id) REFERENCES Sales_Region(region_id)
    );

    CREATE TABLE IF NOT EXISTS Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date DATE NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS Products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price DECIMAL(10,2) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Order_Items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        region_id INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES Orders(order_id),
        FOREIGN KEY (product_id) REFERENCES Products(product_id),
        FOREIGN KEY (region_id) REFERENCES Sales_Region(region_id)
    );

    CREATE TABLE IF NOT EXISTS Marketing_Campaigns (
        campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_name TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Campaign_Performance (
        campaign_id INTEGER NOT NULL,
        impressions INTEGER NOT NULL,
        clicks INTEGER NOT NULL,
        conversions INTEGER NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES Marketing_Campaigns(campaign_id)
    );

    CREATE TABLE IF NOT EXISTS Customer_Feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        feedback_text TEXT NOT NULL,
        rating INTEGER CHECK(rating BETWEEN 1 AND 5),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS Sales_Team_Assignments (
        sales_rep_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        FOREIGN KEY (sales_rep_id) REFERENCES Sales_Team(sales_rep_id),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
    );
""")

# Insert Sample Data

# 1. Insert Sales Regions
regions = ["North America", "Europe", "Asia", "South America", "Australia"]
cursor.executemany("INSERT OR IGNORE INTO Sales_Region (region_name) VALUES (?)", [(r,) for r in regions])

# 2. Insert Customers
customers = []
for _ in range(1000):
    name = fake.name()
    email = fake.unique.email()
    phone = fake.unique.phone_number()
    region = random.choice(regions)
    customers.append((name, email, phone, region))
cursor.executemany("INSERT INTO Customers (name, email, phone_number, region) VALUES (?, ?, ?, ?)", customers)

# 3. Insert Sales Team
sales_team = []
cursor.execute("SELECT region_id FROM Sales_Region")
region_ids = [row[0] for row in cursor.fetchall()]
for _ in range(50):
    name = fake.name()
    region_id = random.choice(region_ids)
    sales_team.append((name, region_id))
cursor.executemany("INSERT INTO Sales_Team (name, region_id) VALUES (?, ?)", sales_team)

# 4. Insert Products
products = [
    ("RTX 4090", "GPU", 1599.99),
    ("RTX 4080", "GPU", 1199.99),
    ("RTX 4070", "GPU", 799.99),
    ("Gaming Laptop", "Laptop", 2499.99),
    ("Workstation PC", "Desktop", 3499.99)
]
cursor.executemany("INSERT INTO Products (product_name, category, price) VALUES (?, ?, ?)", products)

# 5. Insert Orders
orders = []
cursor.execute("SELECT customer_id FROM Customers")
customer_ids = [row[0] for row in cursor.fetchall()]
for _ in range(500):
    customer_id = random.choice(customer_ids)
    order_date = fake.date_this_year()
    total_amount = round(random.uniform(500, 5000), 2)
    orders.append((customer_id, order_date, total_amount))
cursor.executemany("INSERT INTO Orders (customer_id, order_date, total_amount) VALUES (?, ?, ?)", orders)

# 6. Insert Order Items
order_items = []
cursor.execute("SELECT order_id FROM Orders")
order_ids = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT product_id FROM Products")
product_ids = [row[0] for row in cursor.fetchall()]
for _ in range(1000):
    order_id = random.choice(order_ids)
    product_id = random.choice(product_ids)
    quantity = random.randint(1, 5)
    region_id = random.choice(region_ids)  # Associate each order item with a sales region
    order_items.append((order_id, product_id, quantity, region_id))
cursor.executemany("INSERT INTO Order_Items (order_id, product_id, quantity, region_id) VALUES (?, ?, ?, ?)", order_items)

# 7. Insert Marketing Campaigns
campaigns = []
for _ in range(10):
    campaign_name = fake.catch_phrase()
    start_date = fake.date_this_year()
    end_date = fake.date_between(start_date, "+30d")
    campaigns.append((campaign_name, start_date, end_date))
cursor.executemany("INSERT INTO Marketing_Campaigns (campaign_name, start_date, end_date) VALUES (?, ?, ?)", campaigns)

# 8. Insert Campaign Performance
cursor.execute("SELECT campaign_id FROM Marketing_Campaigns")
campaign_ids = [row[0] for row in cursor.fetchall()]
performance_data = [(cid, random.randint(1000, 10000), random.randint(100, 1000), random.randint(10, 500)) for cid in campaign_ids]
cursor.executemany("INSERT INTO Campaign_Performance (campaign_id, impressions, clicks, conversions) VALUES (?, ?, ?, ?)", performance_data)

# 9. Insert Customer Feedback
feedback = [(random.choice(customer_ids), fake.sentence(), random.randint(1, 5)) for _ in range(300)]
cursor.executemany("INSERT INTO Customer_Feedback (customer_id, feedback_text, rating) VALUES (?, ?, ?)", feedback)

# 10. Insert Sales Team Assignments
cursor.execute("SELECT sales_rep_id FROM Sales_Team")
sales_rep_ids = [row[0] for row in cursor.fetchall()]
assignments = [(random.choice(sales_rep_ids), random.choice(customer_ids)) for _ in range(500)]
cursor.executemany("INSERT INTO Sales_Team_Assignments (sales_rep_id, customer_id) VALUES (?, ?)", assignments)

# Commit and Close
conn.commit()
conn.close()

print("✅ Successfully updated the database!")
