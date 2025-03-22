import os
import json
import sqlite3
import streamlit as st
import openai
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load schema from JSON file
def load_schema_from_json(json_path):
    with open(json_path, "r") as file:
        schema = json.load(file)
    relationships = []
    for table, details in schema.items():
        for column in details["columns"]:
            if column["key"] and "Foreign Key" in column["key"]:
                ref_table, ref_column = column["key"].split("?")[1].strip().split(".")
                relationships.append({"table": table, "column": column["name"], "ref_table": ref_table, "ref_column": ref_column})
    return schema, relationships

schema_definitions, schema_relationships = load_schema_from_json("schema.json")
print("schema_relationships",schema_relationships)
valid_tables = set(schema_definitions.keys())

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def get_schema_info(question):
    """Retrieve relevant schema details for a given question using embeddings."""
    table_info = []
    all_texts = []
    index_map = {}

    # Prepare text data for embedding comparison
    index = 0
    for table, details in schema_definitions.items():
        for col in details["columns"]:
            text = f"Table: {table}, Column: {col['name']}, Type: {col['type']}, Desc: {col['description']}"
            all_texts.append(text)
            index_map[index] = text
            table_info.append(col)
            index += 1
    
    # Compute embeddings
    query_embedding = embedding_model.encode(question, convert_to_numpy=True)
    schema_embeddings = embedding_model.encode(all_texts, convert_to_numpy=True)
    
    # Find the most relevant schema details
    scores = np.dot(schema_embeddings, query_embedding)
    top_matches = np.argsort(scores)[-5:][::-1]  # Get top 5 matches
    
    relevant_schema = [index_map[i] for i in top_matches]
    print("\n".join(relevant_schema))
    return "\n".join(relevant_schema)

def validate_sql_relationships(sql):
    """Validate if the relationships in the SQL query match the schema relationships."""
    for rel in schema_relationships:
        if f"{rel['table']}.{rel['column']}" in sql and f"{rel['ref_table']}.{rel['ref_column']}" in sql:
            return True
    return False

def get_openai_response(question, schema_info):
    # """Generate SQL query based on user question and schema info, ensuring only schema-defined tables are used."""
    # prompt = f"""
    
    # You are an expert in SQL generation. Use the following schema details to generate an SQL query:
    # \n{schema_info}\n
    # Ensure that the generated SQL query only references tables from the provided schema.
    # Do not use tables that are not explicitly mentioned.
    
    # Question: {question}

    # The return should contain only sql and donot include ```
    # Use database nvidia_sales
    # """
    prompt = f"""
    You are an expert in converting English questions to SQL query!
    \n\nFor example,\nExample 1 - How many entries of records are present in Customers table?, 
    the SQL command will be something like this SELECT COUNT(*) FROM Customers ;
    \nExample 2 - Tell me how many orders are placed for each product?, 
    the SQL command will be something like this SELECT product_name, count(*) FROM orders o join order_item oi on o.order_id=oi.order_id 
    join Products p on p.product_id = oi.product_id group by product_name;
    
    Use the following schema details table and column name to generate an SQL query:
    \n{schema_info}\n
    Ensure that the generated SQL query only references tables from the provided schema.
    Do not use tables that are not explicitly mentioned.
    Question: {question}

    Print only SQL query without additional text also the sql code should not have ``` in beginning or end and sql word in output"""
    
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in SQL generation."},
            {"role": "user", "content": prompt}
        ]
    )
    
    sql_query = response.choices[0].message.content.strip()
    print(sql_query)
    
    if validate_sql_relationships(sql_query):
        return sql_query
    return "Error: Generated SQL contains invalid relationships. Please try again."

def execute_sql(sql):
    """Execute SQL query in SQLite (Replace with AWS Athena API call)."""
    conn = sqlite3.connect("nvidia_sales.db")
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        print(row)
    return rows

# Streamlit App
st.set_page_config(page_title="RAG-Enhanced Text-to-SQL")
st.header("SQL Query Generator with RAG")

question = st.text_input("Enter your query:")
submit = st.button("Generate SQL")

if submit:
    schema_info = get_schema_info(question)
    sql_query = get_openai_response(question, schema_info)
    st.subheader("Generated SQL:")
    st.code(sql_query, language='sql')
    
    # Execute query (Optional: Replace with AWS Athena execution)
    if "Error:" not in sql_query:
        results = execute_sql(sql_query)
        st.subheader("Query Results:")
        st.write(results)
    else:
        st.error(sql_query)
