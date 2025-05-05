from shin import calculate_implied_probabilities
import pandas as pd

# Read the CSV file
<<<<<<< HEAD
file_path = 'preds.csv'
=======
file_path = 'preds_updated.csv'
>>>>>>> 9f05b0502cab4233bf24e39fdb43f284cde501d3
df = pd.read_csv(file_path)

# Iterate over each row to calculate implied probabilities and update ps_prob
for index, row in df.iterrows():
    psa, psb = row['PSA'], row['PSB']
    probabilities = calculate_implied_probabilities([psa, psb])
    df.at[index, 'ps_prob'] = probabilities[0]

# Fill NaN values in the Awin column with 0 before converting to integers
df['Awin'] = df['Awin'].fillna(0).astype(int)

# Save the updated DataFrame back to the CSV
<<<<<<< HEAD
updated_file_path = 'preds.csv'
=======
updated_file_path = 'preds_updated_updated.csv'
>>>>>>> 9f05b0502cab4233bf24e39fdb43f284cde501d3
df.to_csv(updated_file_path, index=False)

print(f"Updated CSV saved to {updated_file_path}")
