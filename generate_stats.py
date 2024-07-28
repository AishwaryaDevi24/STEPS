import json

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def calculate_stats(data, key):
    total_queries = len(data)
    correct_queries = sum(1 for item in data if item[key] > 0.8)
    avg_score = sum(item[key] for item in data) / total_queries if total_queries > 0 else 0
    highest_score = max(item[key] for item in data) if total_queries > 0 else 0
    lowest_score = min(item[key] for item in data) if total_queries > 0 else 0

    return {
        "total_queries": total_queries,
        "correct_queries": correct_queries,
        "avg_score": avg_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score
    }

def calculate_increased_scores(data):
    increased_count = sum(1 for item in data if item['score_with_nli'] > item['score_without_nli'])
    return increased_count

def print_stats(stats, label):
    print(f"{label}:")
    print(f"Total Number of Queries: {stats['total_queries']}")
    print(f"Correct Queries (Similarity Score > 0.8): {stats['correct_queries']}")
    print(f"Average Similarity Score: {stats['avg_score']:.4f}")
    print(f"Highest Similarity Score: {stats['highest_score']:.4f}")
    print(f"Lowest Similarity Score: {stats['lowest_score']:.4f}")
    print()

def compare_stats(stats1, stats2, label1, label2):
    better_model = label1 if stats1['avg_score'] > stats2['avg_score'] else label2
    print(f"{label1} vs {label2}: Better model is {better_model}\n")

def main():
    llama3_data = load_json('final_results/llama3.json')
    gpt4o_data = load_json('final_results/gpt-4o-mini.json')

    stats_without_nli_llama3 = calculate_stats(llama3_data, 'score_without_nli')
    stats_with_nli_llama3 = calculate_stats(llama3_data, 'score_with_nli')
    stats_without_nli_gpt4o = calculate_stats(gpt4o_data, 'score_without_nli')
    stats_with_nli_gpt4o = calculate_stats(gpt4o_data, 'score_with_nli')

    increased_scores_llama3 = calculate_increased_scores(llama3_data)
    increased_scores_gpt4o = calculate_increased_scores(gpt4o_data)

    print("Comparison of SQL Query Generation with and without NLI Verification")
    print_stats(stats_without_nli_llama3, "Without NLI Verification (Llama3)")
    print_stats(stats_with_nli_llama3, "With NLI Verification (Llama3)")
    print_stats(stats_without_nli_gpt4o, "Without NLI Verification (GPT-4o-mini)")
    print_stats(stats_with_nli_gpt4o, "With NLI Verification (GPT-4o-mini)")

    print(f"Llama3: Number of queries with increased scores after NLI: {increased_scores_llama3}")
    print(f"GPT-4o-mini: Number of queries with increased scores after NLI: {increased_scores_gpt4o}")
    print()

    compare_stats(stats_without_nli_llama3, stats_with_nli_llama3, "Without NLI (Llama3)", "With NLI (Llama3)")
    compare_stats(stats_without_nli_gpt4o, stats_with_nli_gpt4o, "Without NLI (GPT-4o-mini)", "With NLI (GPT-4o-mini)")

    stats_llama3 = calculate_stats(llama3_data, 'score_without_nli')
    stats_gpt4o = calculate_stats(gpt4o_data, 'score_without_nli')

    print("Comparison of SQL Query Generation for Llama3 and GPT-4o-mini")
    print_stats(stats_llama3, "Llama3")
    print_stats(stats_gpt4o, "GPT-4o-mini")

    compare_stats(stats_llama3, stats_gpt4o, "Llama3", "GPT-4o-mini")

if __name__ == "__main__":
    main()
