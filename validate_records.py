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
    data=cursor.execute(f"""SELECT mc.campaign_name, CAST(cp.conversions AS REAL) / cp.clicks AS conversion_rate FROM Marketing_Campaigns mc JOIN Campaign_Performance cp ON mc.campaign_id = cp.campaign_id WHERE cp.clicks > 0 ORDER BY conversion_rate DESC LIMIT 3;""")
    for row in data:
        print(f"{row}")    
    

#close Connection
conn.commit()
conn.close()
