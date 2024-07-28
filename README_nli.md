This folder implements an approach to generate and verify SQL queries using Natural Language Inference (NLI). The core idea is to enhance the quality of automatically generated SQL queries by verifying and correcting them through an NLI model. 

# Files
1. nli_helpers.py: Contains functions for generating explanations for SQL queries using SQL2NL, verifying them using the NLI model and generating necessary corrections.
2. run_sql_nli.py: The main script that orchestrates the SQL query generation, verification, and evaluation processes.
3. dataset/table_schemas.txt: Contains the database schemas used for query generation.
4. dataset/sample_dataset_50.json: Contains questions and expected queries from Spider dataset.
5. dataset/extract_schema.py: Extracts table schema from table_schemas.txt.
6. dataset/extract_qn_query.py: Extracts {question, expected_query} pairs from sample_dataset_50.json.
7. dataset/final_1_10.txt: Contains the questions and expected SQL queries for evaluation.
8. final_results/llama3.json: Stores the results of the comparison between generated and expected queries from Llama3.
9. final_results/gpt-4o-mini.json: Stores the results of the comparison between generated and expected queries from GPT-4o-mini.
10. generate_stats.py: Generates results of scores before and after NLI verification,

# Usage
1. Rename .env_example to .env and place your API keys in that file.
2. Load Schemas and Questions: Ensure the table_schemas.txt and final_1_10.txt files are populated with the appropriate data.
3. Run the Script: Execute the run_sql.py script to generate and verify SQL queries.
4. View Results: Execute generate_stats.py. The results will be stored in final_results/llama3.json and final_results/gpt-4o-mini.json.

# Evaluation
The evaluation compares the generated SQL queries with the expected queries using similarity scores. The evaluation metrics include:
1. Total Number of Queries
2. Number of Correct Queries (Similarity Score > 0.8)
3. Average Similarity Score
4. Highest and Lowest Similarity Scores