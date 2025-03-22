import sqlite3

# Connect to SQLite database
db_name = "nvidia_sales.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

table_list = [
'Customers',
'Orders',
'Products',
'Order_Items',
'Marketing_Campaigns',
'Campaign_Performance',
'Sales_Region',
'Sales_Team',
'Customer_Feedback'
]

for tbl_nm in table_list:
    # data=cursor.execute(f"select count(*) from {tbl_nm}")
    # for row in data:
    #     print(f"{tbl_nm} : {row[0]} records")
    data=cursor.execute(f"""SELECT p.product_name, AVG(cf.rating) AS average_rating
FROM Customer_Feedback cf
JOIN Customers c ON cf.customer_id = c.customer_id
JOIN Products p ON c.product_id = p.product_id
GROUP BY p.product_name;
""")
    for row in data:
        print(f"{row}")    
    

#close Connection
conn.commit()
conn.close()
