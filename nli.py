import json
from llamaapi import LlamaAPI
from transformers import pipeline
from SQL2NL_clean import sql2nl

# Initialize the SDK
llama = LlamaAPI(
    "LL-sjvtytMVBEJ991IY2VgtBpEYYwxO5A9dyqxtYWdZM9zbtp4iQCq2jx1mGQVo5CUZ")

# Initialize the NLI model
nli_model = pipeline("zero-shot-classification",
                     model="facebook/bart-large-mnli")

# question = "List all employees who are older than 45."


def get_sql_query(question):
    # TODO: Provide proper prompt with tables info.
    api_request_json = {
        "model": "llama3-70b",
        "messages": [
            {"role": "system", "content": f"{question} Return the query alone."},
        ]
    }

    response = llama.run(api_request_json)
    # print("FIRST RESPONSE:", json.dumps(response.json(), indent=2))
    # print(response.json().choices[0].message.content)
    content = response.json()['choices'][0]['message']['content']
    result_query = content.strip().strip('```').strip()
    print("CONTENT: ", result_query)

    return result_query

def get_sql_explanation(query):
    sql_explanation = sql2nl(query)  # Generate explanation data
    # print("EXPLANATION: ", sql_explanation[0]['explanation'])
    explanation = sql_explanation[0]['explanation']

    # explanation = [
    #     {'subexpression': 'FROM employees', 'explanation': 'In table managers'},
    #     {'subexpression': 'WHERE age > 45',
    #         'explanation': 'Keep the records where the age is greater than 45'},
    #     {'subexpression': 'SELECT *', 'explanation': 'Return all the records'}
    # ]
    return explanation


def verify_sql_with_nli(question, sql_explanation):
    results = []
    for step in sql_explanation:
        result = nli_model(sequences=question, candidate_labels=[
                           step['explanation']])
        results.append({
            'subexpression': step['subexpression'],
            'explanation': step['explanation'],
            'label': result['labels'][0],
            'score': result['scores'][0]
        })
    return results


def correct_sql_steps(nli_results, question):
    corrected_steps = []
    needs_correction = False
    final_score = 0
    for result in nli_results:
        counter = 0
        if result['score'] < 0.8:
            needs_correction = True
            corrected_explanation = generate_correction(result['explanation'], question)
            for _ in range(5):  # Run the loop up to 5 times
                counter += 1
                print("Iteration ", counter)
                verification_result = nli_model(sequences=question, candidate_labels=[corrected_explanation])
                if verification_result['scores'][0] > 0.8:
                    # final_score += verification_result['scores'][0]
                    break
                corrected_explanation = generate_correction(corrected_explanation, question)
            corrected_steps.append({
                'subexpression': result['subexpression'],
                'original_explanation': result['explanation'],
                'corrected_explanation': corrected_explanation
            })
        else:
            corrected_steps.append({
                'subexpression': result['subexpression'],
                'explanation': result['explanation'],
            })
    
    if not needs_correction:
        return "No correction needed. All steps are correct."
    
    return corrected_steps


def generate_correction(explanation, question):
    prompt = f"This step is wrong: '{explanation}'. Please verify with the question: '{question}' and provide a corrected step and corresponding correction to the SQL query."

    # Re-run the LLM
    api_request_json = {
        "model": "llama3-70b",
        "messages": [
            {"role": "system", "content": prompt},
        ]
    }
    response = llama.run(api_request_json)
    # print("correction123:", json.dumps(response.json(), indent=2))
    # print(response.json().choices[0].message.content)
    explanation = response.json()['choices'][0]['message']['content']
    corrected_explanation = explanation
    print("CORRECTION: ", corrected_explanation)
    return corrected_explanation


# sql_query = get_sql_query(question)
# sql_explanation = get_sql_explanation(sql_query)
# nli_results = verify_sql_with_nli(question, sql_explanation)

# for result in nli_results:
#     print(f"Step: {result['subexpression']}")
#     print(f"Explanation: {result['explanation']}")
#     print(f"Label: {result['label']}, Score: {result['score']}\n")

# correction_result = correct_sql_steps(nli_results, question)

# if isinstance(correction_result, str):
#     print(correction_result)
# else:
#     for step in correction_result:
#         if 'corrected_explanation' in step:
#             print(f"Original: {step['original_explanation']}")
#             print(f"Corrected: {step['corrected_explanation']}\n")
#         else:
#             print(f"Explanation: {step['explanation']}")
