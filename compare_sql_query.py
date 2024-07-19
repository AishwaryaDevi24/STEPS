import json
from nli import get_sql_explanation, verify_sql_with_nli, correct_sql_steps
import re

from llamaapi import LlamaAPI
llama = LlamaAPI("LL-sjvtytMVBEJ991IY2VgtBpEYYwxO5A9dyqxtYWdZM9zbtp4iQCq2jx1mGQVo5CUZ")

def load_schemas_from_file(file_path):
    schemas = {}
    with open(file_path, 'r') as f:
        lines = f.readlines()
        current_db_id = None
        current_table = None

        for line in lines:
            line = line.strip()
            if line.startswith("Database ID:"):
                current_db_id = line.split(":")[1].strip()
                if current_db_id not in schemas:
                    schemas[current_db_id] = {}
            elif line.startswith("Table Name:"):
                current_table = line.split(":")[1].strip()
                schemas[current_db_id][current_table] = []
            elif line.startswith("-"):
                column_info = line.split("(", 1)
                column_name = column_info[0].strip("- ").strip()
                column_type = column_info[1].strip(")").strip()
                schemas[current_db_id][current_table].append((column_name, column_type))
    return schemas

def get_relevant_schema(schemas, db_id):
    if db_id in schemas:
        return schemas[db_id]
    else:
        return None

def get_final_query(result):
    prompt = f"Return the final correct sql query alone without any extra words from the corrected_explanation key in the following object: {result}. Ignore the semicolon at the end of the query."
    api_request_json = {
        "model": "llama3-70b",
        "messages": [
            {"role": "system", "content": prompt},
        ]
    }
    response = llama.run(api_request_json)
    data = response.json()
    content = data.get('choices', [])[0].get('message', {}).get('content', '')

    # Remove the surrounding backticks and newlines
    sql_query = content.strip('`\n')
    print("hi ", sql_query)
    return sql_query

def construct_prompt_with_schema(question, schema):
    prompt = "Given the following database schema and a question, generate the correct SQL query to answer the question. The schema contains table names and their respective columns with data types. Please ensure the SQL query is accurate and syntactically correct.\n\n"
    prompt += "Database Schema:\n"
    for table_name, columns in schema.items():
        prompt += f"Table: {table_name}\n"
        for column in columns:
            prompt += f"  - {column[0]} ({column[1]})\n"
    prompt += f"\nQuestion: {question}\n\n"
    prompt += "Return only the SQL query."
    return prompt

def get_sql_query_with_schema(llama, question, schema):
    prompt = construct_prompt_with_schema(question, schema)
    api_request_json = {
        "model": "llama3-70b",
        "messages": [
            {"role": "system", "content": prompt},
        ]
    }
    response = llama.run(api_request_json)
    content = response.json()['choices'][0]['message']['content']
    result_query = content.strip().strip('```').strip().replace('\n', ' ')
    return result_query

def load_questions_from_file(file_path):
    queries = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        current_db_id = None
        current_question = None
        current_sql_query = None
        for line in lines:
            line = line.strip()
            if line.startswith("Database ID:"):
                current_db_id = line.split(":")[1].strip()
            elif line.startswith("Question:"):
                current_question = line.split(":")[1].strip()
            elif line.startswith("SQL Query:"):
                current_sql_query = line.split(":")[1].strip()
                if current_db_id and current_question and current_sql_query:
                    queries.append((current_db_id, current_question, current_sql_query))
                current_db_id = None
                current_question = None
                current_sql_query = None
    return queries

def normalize_query(q):
    q = q.strip()
    q = re.sub(r'\s+', ' ', q)
    q = re.sub(r'\s([?.!,])', r'\1', q)
    q = q.lower()
    return q

def compare_queries(expected_query, generated_query):
    return (normalize_query(expected_query) == normalize_query(generated_query))

def compare_sql_query_with_verification(output_file):
    results = []
    for db_id, question, expected_query in questions:
        relevant_schema = get_relevant_schema(schemas, db_id)
        if relevant_schema:
            sql_query = get_sql_query_with_schema(llama, question, relevant_schema)
            original_query = sql_query
            sql_explanation = get_sql_explanation(sql_query)
            print("EXPLANATION: ", sql_explanation)
            nli_results = verify_sql_with_nli(question, sql_explanation)

            # total_score = sum(result['score'] for result in nli_results)
            # print(f"Total Score: {total_score}\n")

            for result in nli_results:
                print(f"Step: {result['subexpression']}")
                print(f"Explanation: {result['explanation']}")
                print(f"Label: {result['label']}, Score: {result['score']}\n")

            correction_result = correct_sql_steps(nli_results, question)

            final_sql_query = sql_query  

            if isinstance(correction_result, list):
                print("here")
                print("*********")
                print("CORRECTION RESULT: ", correction_result)
                print("*********")
                final_sql_query = get_final_query(correction_result).replace('\n', ' ')

            print(f"Database ID: {db_id}")
            print(f"Question: {question}")
            print(f"Expected SQL Query: {expected_query}")
            print(f"Final SQL Query: {final_sql_query}")
            comparison_result = compare_queries(expected_query, final_sql_query)
            if comparison_result:
                print("The generated SQL query matches the expected query.\n")
            else:
                print("The generated SQL query does NOT match the expected query.\n")

            results.append({
                'database_id': db_id,
                'question': question,
                'expected_query': normalize_query(expected_query),
                'generated_query_without_nli': normalize_query(original_query),
                'generated_query_with_nli': normalize_query(final_sql_query),
                # 'total_score': total_score,
                'match': comparison_result
            })
        else:
            print(f"No schema found for db_id: {db_id}\n")

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

schema_file_path = 'dataset/table_schemas.txt'
question_file_path = 'dataset/qn_query_pairs_5.txt'
output_file_path = 'dataset/comparison_results.json'

schemas = load_schemas_from_file(schema_file_path)

questions = load_questions_from_file(question_file_path)

compare_sql_query_with_verification(output_file_path)
