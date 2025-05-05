import pandas as pd
import numpy as np

# Load the datasets
try:
    df_preds = pd.read_csv('preds.csv')
    df_atp = pd.read_csv('atp.csv')
    print("Files loaded successfully.")
except FileNotFoundError as e:
    print(f"Error loading files: {e}. Make sure both 'preds.csv' and 'atp.csv' are in the correct directory.")
    exit()
except Exception as e:
    print(f"An error occurred loading the CSV files: {e}")
    exit()

# --- Data Cleaning and Preparation ---
# Select relevant columns and handle potential missing values in key columns
df_atp_relevant = df_atp[['winner_name', 'loser_name', 'PSW', 'PSL']].dropna(subset=['winner_name', 'loser_name'])
df_preds_original_cols = df_preds.columns.tolist() # Keep original order

# Ensure player name columns are string type for reliable merging
df_preds['A'] = df_preds['A'].astype(str)
df_preds['B'] = df_preds['B'].astype(str)
df_atp_relevant['winner_name'] = df_atp_relevant['winner_name'].astype(str)
df_atp_relevant['loser_name'] = df_atp_relevant['loser_name'].astype(str)

# Add a temporary index to track rows in preds
df_preds['pred_idx'] = range(len(df_preds))

# --- Merge Logic ---

# Merge 1: Find matches where preds['A'] is the winner in atp
merged_A_wins = pd.merge(
    df_preds[['pred_idx', 'A', 'B']],
    df_atp_relevant,
    left_on=['A', 'B'],
    right_on=['winner_name', 'loser_name'],
    how='left'
)
# In case of multiple matches in ATP for the same pair, keep the first one
merged_A_wins = merged_A_wins.drop_duplicates(subset=['pred_idx'], keep='first')
# Filter for actual matches found
matches_A_won = merged_A_wins[merged_A_wins['winner_name'].notna()].set_index('pred_idx')

# Merge 2: Find matches where preds['B'] is the winner in atp (A is loser)
merged_B_wins = pd.merge(
    df_preds[['pred_idx', 'A', 'B']],
    df_atp_relevant,
    left_on=['A', 'B'],
    right_on=['loser_name', 'winner_name'],
    how='left'
)
# Keep the first match if duplicates exist
merged_B_wins = merged_B_wins.drop_duplicates(subset=['pred_idx'], keep='first')
# Filter for actual matches found
matches_B_won = merged_B_wins[merged_B_wins['winner_name'].notna()].set_index('pred_idx')


# --- Update df_preds ---

# Initialize new/updated columns in df_preds
# Use existing columns if they exist, otherwise create them
for col in ['PSA', 'PSB', 'Awin']:
    if col not in df_preds.columns:
        df_preds[col] = np.nan

# Set index for easier updating
df_preds = df_preds.set_index('pred_idx')

# Update based on matches where A won
df_preds.loc[matches_A_won.index, 'Awin'] = 1
df_preds.loc[matches_A_won.index, 'PSA'] = matches_A_won['PSW']
df_preds.loc[matches_A_won.index, 'PSB'] = matches_A_won['PSL']

# Update based on matches where B won
df_preds.loc[matches_B_won.index, 'Awin'] = 0
# Note: When B wins, A's odds (PSA) correspond to the loser's odds (PSL) in ATP
df_preds.loc[matches_B_won.index, 'PSA'] = matches_B_won['PSL']
# Note: When B wins, B's odds (PSB) correspond to the winner's odds (PSW) in ATP
df_preds.loc[matches_B_won.index, 'PSB'] = matches_B_won['PSW']

# --- Identify and Report Unmatched Rows ---
unmatched_mask = df_preds['Awin'].isna()
unmatched_preds = df_preds[unmatched_mask]

print("\n--- Unmatched Rows ---")
if unmatched_preds.empty:
    print("All rows in preds.csv were matched successfully!")
else:
    print(f"Found {len(unmatched_preds)} rows in preds.csv that could not be matched in atp.csv:")
    # Display only the key columns for clarity
    print(unmatched_preds[['A', 'B']].to_string())

# --- Final Cleanup and Output ---
# Reset index to remove pred_idx as the index
df_preds = df_preds.reset_index(drop=True)

# Ensure Awin is integer where possible (NaNs will remain float)
df_preds['Awin'] = df_preds['Awin'].astype('Int64') # Use nullable integer type

# Ensure odds are float
df_preds['PSA'] = pd.to_numeric(df_preds['PSA'], errors='coerce')
df_preds['PSB'] = pd.to_numeric(df_preds['PSB'], errors='coerce')

# Reorder columns to match original preds.csv plus the updated ones
# Define the desired final column order
final_columns = df_preds_original_cols.copy()
# Remove potentially duplicated/updated columns from original list
for col in ['PSA', 'PSB', 'Awin', 'ps_prob']:
     if col in final_columns:
         final_columns.remove(col)

# Add the columns back in the desired order
final_columns.extend(['PSA', 'PSB', 'Awin', 'ps_prob'])

# Filter out any columns not actually present (like ps_prob if it wasn't there)
final_columns = [col for col in final_columns if col in df_preds.columns]

# Reindex the DataFrame
df_preds_final = df_preds[final_columns]

df_preds_final.to_csv('preds_merged.csv', index=False)
print("\nUpdated DataFrame saved to 'preds_merged.csv'")
