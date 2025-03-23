import os
import json
import sqlite3
import streamlit as st
import openai
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import csv

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
valid_tables = set(schema_definitions.keys())

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# def get_schema_info(question):
#     """Retrieve relevant schema details for a given question using embeddings."""
#     table_info = []
#     all_texts = []
#     index_map = {}

#     # Prepare text data for embedding comparison
#     index = 0
#     for table, details in schema_definitions.items():
#         for col in details["columns"]:
#             text = f"Table: {table}, Column: {col['name']}, Type: {col['type']}, Desc: {col['description']}"
#             all_texts.append(text)
#             index_map[index] = text
#             table_info.append(col)
#             index += 1
    
#     # Compute embeddings
#     query_embedding = embedding_model.encode(question, convert_to_numpy=True)
#     schema_embeddings = embedding_model.encode(all_texts, convert_to_numpy=True)
    
#     # Find the most relevant schema details
#     scores = np.dot(schema_embeddings, query_embedding)
#     top_matches = np.argsort(scores)[-5:][::-1]  # Get top 5 matches
    
#     relevant_schema = [index_map[i] for i in top_matches]
#     print("\n".join(relevant_schema))
#     return "\n".join(relevant_schema)

def validate_sql_relationships(sql):
    """Validate if the relationships in the SQL query match the schema relationships."""
    for rel in schema_relationships:
        if f"{rel['table']}.{rel['column']}" in sql and f"{rel['ref_table']}.{rel['ref_column']}" in sql:
            return True
    return False


def read_table_metadata(csv_path):
    """Read table metadata from a CSV file and format it for input."""
    metadata = []
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            metadata.append({
                "table_name": row["Table Name"],
                "column_name": row["Column Name"],
                "data_type": row["Data Type"],
                "key": row["Key"],
                "description": row["Description"]
            })
    return metadata

print(read_table_metadata("table_metadata.csv"))

def get_openai_response(question, schema_relationships=schema_relationships, metadata_details=read_table_metadata("table_metadata.csv")):
    # Format metadata as a string for the prompt
    metadata_string = "\n".join(
        f"Table: {row['table_name']}, Column: {row['column_name']}, Type: {row['data_type']}, Key: {row['key']}, Desc: {row['description']}"
        for row in metadata_details
    )
    
    prompt = f"""
You are an expert in converting natural language questions into SQLite SQL queries. Use the schema details below to generate an accurate SQL query. 

Examples:
1. Question: How many records are in the Customers table?
   JSON: {{"query_description": "Counts the records in the Customers table.", "sql": "SELECT COUNT(*) FROM Customers;"}}

2. Question: Show the total orders per product.
   JSON: {{"query_description": "Retrieves total orders grouped by product name.", "sql": "SELECT product_name, COUNT(*) FROM orders o JOIN order_items oi ON o.order_id = oi.order_id GROUP BY product_name;"}}

    Question: {question}

 Refine your answer based on instructions:
- Validate if the columns are part of table definitions for each table used in the SQL query {metadata_string}
- Validate joins using foreign key relationships in the schema. \n {schema_relationships} \n   

    Your response should be a JSON object with the following structure:
    {{
        "query_description": "A short description of what the query does",
        "sql": "Generated SQL query"
    }}
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in SQL generation."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract JSON response
    response_content = response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
    print("response_content",response_content)
    try:
        response_json = json.loads(response_content)
        sql_query = response_json.get("sql", "")
        query_description = response_json.get("query_description", "")
    except json.JSONDecodeError:
        return {"error": "Failed to parse the JSON response from OpenAI."}
    
    print("question",question)
    
    print({"query_description": query_description, "sql": sql_query})
    return {"query_description": query_description, "sql": sql_query}
    # Validate relationships in SQL
    # if validate_sql_relationships(sql_query):
    #     return {"query_description": query_description, "sql": sql_query}
    # else:
    #     return {"error": "Generated SQL contains invalid relationships. Please try again."}

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

# Initialize session state variables
if "acknowledged" not in st.session_state:
    st.session_state["acknowledged"] = False  # Tracks if the user acknowledged the query
if "results" not in st.session_state:
    st.session_state["results"] = None  # Stores the SQL query results
if "response" not in st.session_state:
    st.session_state["response"] = None  # Stores the generated SQL response

# Streamlit App
st.set_page_config(page_title="RAG-Enhanced Text-to-SQL")
st.header("SQL Query Generator with RAG")

question = st.text_input("Enter your query:")
submit = st.button("Generate SQL")

# Step 1: Generate SQL when the user clicks the submit button
if submit:
    # schema_info = get_schema_info(question)
    response = get_openai_response(question)

    if "error" in response:
        st.error(response["error"])
        st.session_state["response"] = None
    else:
        st.session_state["response"] = response
        st.session_state["acknowledged"] = False  # Reset acknowledgment for a new query

# Step 2: Display the generated SQL query and wait for acknowledgment
if st.session_state["response"]:
    st.subheader("Generated Output:")
    st.json(st.session_state["response"])

    # Ask for user acknowledgment
    acknowledge = st.checkbox("I acknowledge that the SQL query is correct.")

    if acknowledge and not st.session_state["acknowledged"]:
        st.session_state["acknowledged"] = True
        # Execute the query
        st.session_state["results"] = execute_sql(st.session_state["response"]["sql"])

# Step 3: Display the results if acknowledged
if st.session_state["acknowledged"] and st.session_state["results"]:
    st.subheader("Query Results:")
    st.write(st.session_state["results"])

