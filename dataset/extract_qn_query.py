import json

def load_spider_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def extract_question_query_pairs(data):
    pairs = []
    for item in data:
        db_id = item['db_id']
        question = item['question']
        query = item['query']
        pairs.append((db_id, question, query))
    return pairs

def save_pairs_to_file(pairs, output_file):
    with open(output_file, 'w') as f:
        for db_id, question, query in pairs:
            f.write(f"Database ID: {db_id}\n")
            f.write(f"Question: {question}\n")
            f.write(f"SQL Query: {query}\n\n")

train_file_path = 'dataset/sample_dataset_50_mid.json'

train_data = load_spider_data(train_file_path)

train_pairs = extract_question_query_pairs(train_data)

save_pairs_to_file(train_pairs, 'dataset/qn_query_pairs_50_mid.txt')

print("Question, query pairs, and db_id extracted and saved.")
