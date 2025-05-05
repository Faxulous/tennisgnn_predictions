from shin import calculate_implied_probabilities
import pandas as pd

# Read the CSV file
file_path = 'preds.csv'
df = pd.read_csv(file_path)

# Iterate over each row to calculate implied probabilities and update ps_prob
for index, row in df.iterrows():
    psa, psb = row['PSA'], row['PSB']
    probabilities = calculate_implied_probabilities([psa, psb])
    df.at[index, 'ps_prob'] = probabilities[0]

# Fill NaN values in the Awin column with 0 before converting to integers
df['Awin'] = df['Awin'].fillna(0).astype(int)

# Save the updated DataFrame back to the CSV
updated_file_path = 'preds.csv'
df.to_csv(updated_file_path, index=False)

print(f"Updated CSV saved to {updated_file_path}")
