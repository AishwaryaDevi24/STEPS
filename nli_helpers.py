from transformers import pipeline
from SQL2NL_clean import sql2nl
from llm_switch import call_llm

nli_model = pipeline("zero-shot-classification",
                     model="facebook/bart-large-mnli")

def get_sql_explanation(query):
    try:
        sql_explanation = sql2nl(query)
        explanation = sql_explanation[0]['explanation']
    except Exception as e:
        print("Unable to generate explanation for this query ", e)
    return explanation


def get_nli_score_for_steps(question, sql_explanation):
    results = []
    for step in sql_explanation:
        result = nli_model(sequences=question, candidate_labels=[
                           step['explanation']])
        results.append({
            'subexpression': step['subexpression'],
            'explanation': step['explanation'],
            'score': result['scores'][0]
        })
    return results

def correct_sql_steps(nli_results, question, sql_query, schema):
    needs_correction = False
    iteration_count = 0
    updated_query = sql_query
    while iteration_count < 5:
        iteration_count += 1
        print("Iteration: ", iteration_count)
        all_scores_above_threshold = True

        for result in nli_results:
            if result['score'] < 0.8:
                needs_correction = True
                correction = generate_correction(result['subexpression'], result['explanation'], question, sql_query, schema)
                updated_query = correction['query']
                nli_results = get_nli_score_for_steps(question, correction['explanation'])
                break
        all_scores_above_threshold = all(result['score'] >= 0.8 for result in nli_results)
        if all_scores_above_threshold:
            break

    if not needs_correction:
        return "No correction needed. All steps are correct."
    return [nli_results, updated_query]

def construct_correction_prompt(question, schema, incorrect_subexp, incorrect_step, previous_query):
    prompt = "You are an SQL expert, highly proficient in writing accurate and syntactically correct SQL queries.\n\n"
    prompt += f"The following subexpression in the generated SQL query is incorrect: {incorrect_subexp}.\n"
    prompt += f"The corresponding explanation for the wrong subexpression is: {incorrect_step}.\n"
    prompt += f"Here is the complete SQL query for reference: {previous_query}.\n"
    prompt += "Please review the subexpression with its explanation and provide the corrected sql query considering the following database schema and the question.\n\n"
    
    prompt += f"The database has {len(schema)} tables.\n"
    
    for table_name, columns in schema.items():
        prompt += f"The table {table_name} has the following columns:\n"
        for column in columns:
            prompt += f"  - {column[0]}, which is of type {column[1]}.\n"
    
    prompt += f"\nQuestion: {question}\n\n"
    prompt += "Understand the database schema properly, infer what each table and its columns does from the table name and the column names. Don't make unnecessary joins. Please provide only the corrected SQL query to answer the question with no other extra words."
    return prompt

def generate_correction(subexpression, explanation, question, sql_query, schema):
    prompt = construct_correction_prompt(question, schema, subexpression, explanation, sql_query)
    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": question
        },
        {
            "role": "assistant",
            "content": f"The subexpression {subexpression} with explanation {explanation} is incorrect."
        },
        {
            "role": "user",
            "content": "Please provide new query with the correct subexpression."
        }
    ]
    corrected_query = call_llm(messages)
    print("RESPONSE: ", corrected_query)
    corrected_explanation = get_sql_explanation(corrected_query)
    return {'query': corrected_query, 'explanation': corrected_explanation }
