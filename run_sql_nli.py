import json
from llm_switch import call_llm, set_llm
from nli_helpers import get_sql_explanation, get_nli_score_for_steps, correct_sql_steps
import re
from compare_sql import sql_similarity

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
                schemas[current_db_id][current_table].append(
                    (column_name, column_type))
    return schemas


def get_relevant_schema(schemas, db_id):
    if db_id in schemas:
        return schemas[db_id]
    else:
        return None

def construct_prompt_with_schema(question, schema):
    prompt = "You are an SQL expert, highly proficient in writing accurate and syntactically correct SQL queries.\n\n"
    prompt += "Given the following database schema and a question, generate the correct SQL query to answer the question. The schema contains table names and their respective columns with data types.\n\n"
    prompt += f"The database has {len(schema)} tables.\n"

    for table_name, columns in schema.items():
        prompt += f"The table '{table_name}' has the following columns:\n"
        for column in columns:
            prompt += f"  - {column[0]}, which is of type {column[1]}.\n"

    prompt += f"\nThe question to be answered is: {question}\n\n"
    prompt += "Understand the database schema properly, infer what each table and its columns does from the table name and the column names. Don't make unnecessary joins. Please provide only the SQL query to answer the question with no extra words."
    return prompt

def get_sql_query_with_schema(question, schema):
    prompt = construct_prompt_with_schema(question, schema)
    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": question
        }
    ]
    response = call_llm(messages)
    return response


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
                    queries.append(
                        (current_db_id, current_question, current_sql_query))
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
            expected_query = expected_query + ";" if expected_query[-1] != ";" else expected_query
            relevant_schema = get_relevant_schema(schemas, db_id)
            print("QUESTION: ", question)
            if relevant_schema:
                query_before_verification = get_sql_query_with_schema(
                    question, relevant_schema)
                sql_explanation = get_sql_explanation(
                    query_before_verification)
                nli_results = get_nli_score_for_steps(
                    question, sql_explanation)

                for result in nli_results:
                    print(f"Subexpression: {result['subexpression']}")
                    print(f"Explanation: {result['explanation']}")
                    print(f"Score: {result['score']}\n")

                correction_result, final_query = correct_sql_steps(
                    nli_results, question, query_before_verification, relevant_schema)
                print("CORRECTION RESULT: ", correction_result, final_query)
                nli_testing = {'question': question,
                                'nli_result': correction_result}
                append_to_json_file(nli_file_path, nli_testing)

                print(f"Database ID: {db_id}")
                print(f"Question: {question}")
                print(f"Expected SQL Query: {expected_query}")
                print(f"Final SQL Query: {final_query}")
                comparison_score_before_nli_verification = sql_similarity(
                    expected_query, query_before_verification)
                comparison_score_after_nli_verification = sql_similarity(
                    expected_query, final_query)
                if comparison_score_after_nli_verification > 0.8:
                    print("The generated SQL query matches the expected query.\n")
                else:
                    print(
                        "The generated SQL query does NOT match the expected query.\n")
                results = {
                    'database_id': db_id,
                    'question': question,
                    'expected_query': normalize_query(expected_query),
                    'generated_query_without_nli': normalize_query(query_before_verification),
                    'generated_query_with_nli': normalize_query(final_query),
                    'score_without_nli': comparison_score_before_nli_verification,
                    'score_with_nli': comparison_score_after_nli_verification
                }
            else:
                print(f"No schema found for db_id: {db_id}\n")
            print(results)
            append_to_json_file(output_file, results)

def append_to_json_file(output_file, new_data):
    try:
        with open(output_file, 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    existing_data.append(new_data)

    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

# ["gpt-4o-mini", "llama3"]
llm_var = "llama3"
schema_file_path = 'dataset/table_schemas.txt'
question_file_path = 'dataset/qn_query_pairs_5.txt'
output_file_path = f'final_results/{llm_var}.json'
nli_file_path = 'dataset/nli_testing.json'

schemas = load_schemas_from_file(schema_file_path)

questions = load_questions_from_file(question_file_path)
set_llm("llama3")
compare_sql_query_with_verification(output_file_path)
