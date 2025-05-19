import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
START_DATE = '2022-01-01'
END_DATE = '2025-03-31'
TARGET_SURFACE = 'Clay'
TARGET_LEVELS = ['Grand Slam', 'Masters 1000']
OUTPUT_DIR = 'analysis_output'
MODEL_BETTER_CSV = os.path.join(OUTPUT_DIR, 'model_better_intransitivity.csv')
WELO_BETTER_CSV = os.path.join(OUTPUT_DIR, 'welo_better_intransitivity.csv')
MODEL_BETTER_PLOT = os.path.join(OUTPUT_DIR, 'model_better_prob_diff.png')
COMPREHENSIVE_PLOT = os.path.join(OUTPUT_DIR, 'comprehensive_prob_comparison.png') # New plot filename

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Helper Functions --- (Keep as before)
def parse_date(date_str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try: return datetime.strptime(str(date_str), fmt)
        except (ValueError, TypeError): continue
    return pd.NaT
def normalize_player_name(name):
    if pd.isna(name): return None
    return str(name).strip()

# --- Load and Prepare Data --- (Keep as before)
try:
    preds_df = pd.read_csv('preds.csv')
    if preds_df['Awin'].dtype == 'object':
        preds_df['Awin'] = preds_df['Awin'].astype(str).str.replace('x', '', regex=False).str.strip()
        preds_df['Awin'] = pd.to_numeric(preds_df['Awin'], errors='coerce')
    preds_df.dropna(subset=['Awin'], inplace=True)
    preds_df['Awin'] = preds_df['Awin'].astype(int)
    preds_df['A_norm'] = preds_df['A'].apply(normalize_player_name)
    preds_df['B_norm'] = preds_df['B'].apply(normalize_player_name)
    print(f"Loaded {len(preds_df)} prediction rows.")

    atp_df = pd.read_csv('atp.csv', low_memory=False)
    atp_df['Date'] = atp_df['Date'].apply(parse_date)
    atp_df.dropna(subset=['Date'], inplace=True)
    atp_df['winner_name_norm'] = atp_df['winner_name'].apply(normalize_player_name)
    atp_df['loser_name_norm'] = atp_df['loser_name'].apply(normalize_player_name)
    print(f"Loaded {len(atp_df)} historical ATP rows.")

except FileNotFoundError as e: print(f"Error: File not found: {e.filename}"); exit()
except Exception as e: print(f"An error occurred: {e}"); exit()


# --- Filter Historical Data --- (Keep as before)
start_dt = datetime.strptime(START_DATE, '%Y-%m-%d')
end_dt = datetime.strptime(END_DATE, '%Y-%m-%d')
historical_filtered = atp_df[
    (atp_df['Date'] >= start_dt) & (atp_df['Date'] <= end_dt) &
    (atp_df['Surface'] == TARGET_SURFACE) &
    (atp_df['tourney_level'].isin(TARGET_LEVELS))
].copy()
print(f"Filtered historical data: {len(historical_filtered)} matches (Clay, GS/Masters, 2022-Apr 2025).")
# Only exit if needed for intransitivity check later
# if len(historical_filtered) == 0: print("No relevant historical matches found for intransitivity check.");

# Pre-calculate historical wins for efficiency (even if empty, dict will be empty)
wins_dict = {}
for _, row in historical_filtered.iterrows():
    winner = row['winner_name_norm']
    loser = row['loser_name_norm']
    if winner is None or loser is None: continue
    if winner not in wins_dict: wins_dict[winner] = set()
    wins_dict[winner].add(loser)

# --- Process ALL Matches for Comprehensive Analysis ---
all_matches_analysis = []
preds_df_reset = preds_df.reset_index()

for index, row in preds_df_reset.iterrows():
    original_index = row['index']
    model_prob = row['model_prob']
    welo_prob = row['welo_prob']
    awin = row['Awin']
    player_a_orig = row['A']
    player_b_orig = row['B']
    player_a_norm = row['A_norm']
    player_b_norm = row['B_norm']

    if player_a_norm is None or player_b_norm is None: continue

    model_correct = (model_prob > 0.5 and awin == 1) or (model_prob < 0.5 and awin == 0)
    welo_correct = (welo_prob > 0.5 and awin == 1) or (welo_prob < 0.5 and awin == 0)

    actual_winner_norm = player_a_norm if awin == 1 else player_b_norm
    actual_loser_norm = player_b_norm if awin == 1 else player_a_norm

    # Assign Analysis Case
    if model_correct and not welo_correct: analysis_case = 'Model Only Correct'
    elif not model_correct and welo_correct: analysis_case = 'Welo Only Correct'
    elif model_correct and welo_correct: analysis_case = 'Both Correct'
    else: analysis_case = 'Both Incorrect'

    # Check for Intransitivity Loop for this match
    involved_in_loop = False
    if len(historical_filtered) > 0: # Only check if we have historical data
        players_C = wins_dict.get(actual_loser_norm, set())
        if players_C:
            for player_C in players_C:
                if player_C == actual_winner_norm or player_C is None: continue
                c_wins_over = wins_dict.get(player_C, set())
                if actual_winner_norm in c_wins_over:
                    involved_in_loop = True
                    break # Found one loop, no need to check further for this flag

    all_matches_analysis.append({
        'match_index': index,
        'A_orig': player_a_orig,
        'B_orig': player_b_orig,
        # 'A_norm': player_a_norm, # Not needed directly in final plot df
        # 'B_norm': player_b_norm,
        # 'winner_norm': actual_winner_norm,
        # 'loser_norm': actual_loser_norm,
        'model_prob': model_prob,
        'welo_prob': welo_prob,
        'Awin': awin,
        'analysis_case': analysis_case,
        'involved_in_loop': involved_in_loop
    })

all_matches_df = pd.DataFrame(all_matches_analysis)
print(f"\nProcessed {len(all_matches_df)} matches for comprehensive analysis.")

# --- Generate Comprehensive Visualization ---
if not all_matches_df.empty:
    # Melt the DataFrame for plotting
    melted_df = pd.melt(all_matches_df,
                        id_vars=['match_index', 'analysis_case', 'involved_in_loop'],
                        value_vars=['model_prob', 'welo_prob'],
                        var_name='probability_type',
                        value_name='probability_value')

    print(f"\nGenerating comprehensive comparison plot...")
    try:
        # Define order for categories
        case_order = ['Both Correct', 'Model Only Correct', 'Welo Only Correct', 'Both Incorrect']
        hue_order = ['model_prob', 'welo_prob']

        g = sns.catplot(
            data=melted_df,
            x='analysis_case',
            y='probability_value',
            hue='probability_type',
            col='involved_in_loop',
            kind='box', # Use 'violin' for density shape
            order=case_order,
            hue_order=hue_order,
            palette='muted', # Or choose another palette
            legend=False, # Add legend manually for better placement
            height=5, # Adjust height
            aspect=1.2 # Adjust aspect ratio
        )

        # Set titles and labels
        g.fig.suptitle('Comparison of Model vs Welo Probabilities by Scenario and Intransitivity', y=1.03)
        g.set_axis_labels("Prediction Scenario", "Probability")
        g.set_titles("Intransitivity Involved: {col_name}")
        g.despine(left=True) # Remove left spine
        plt.legend(title='Probability Type', loc='upper right', bbox_to_anchor=(1.15, 1)) # Adjust legend position

        # Adjust layout and save
        plt.tight_layout(rect=[0, 0, 1, 0.97]) # Adjust rect to prevent title overlap
        plt.savefig(COMPREHENSIVE_PLOT)
        print(f"Comprehensive visualization saved to: {COMPREHENSIVE_PLOT}")
        plt.close()

    except Exception as e:
        print(f"Error generating comprehensive visualization: {e}")
else:
    print("Skipping comprehensive visualization (no data).")


# --- Run Previous Analysis for CSVs (Model Better vs Welo Better discrepancy) ---
# Separate lists for the specific discrepancy analysis
model_better_matches_list = [m for m in all_matches_analysis if m['analysis_case'] == 'Model Only Correct']
welo_better_matches_list = [m for m in all_matches_analysis if m['analysis_case'] == 'Welo Only Correct']

def analyze_discrepancy(match_list, analysis_type):
    # (This function is slightly simplified from previous version - only needs to add loop strings)
    if not match_list:
        return None, "N/A"

    df = pd.DataFrame(match_list)

    # Calculate Prob Diff (for discrepancy comparison)
    if analysis_type == 'model_better':
        df['prob_diff'] = df.apply(lambda row: row['model_prob'] - row['welo_prob'] if row['Awin'] == 1 else (1-row['model_prob']) - (1-row['welo_prob']), axis=1)
        prob_diff_desc = "(Model Prob for Winner) - (Welo Prob for Winner)"
    elif analysis_type == 'welo_better':
        df['prob_diff'] = df.apply(lambda row: row['welo_prob'] - row['model_prob'] if row['Awin'] == 1 else (1-row['welo_prob']) - (1-row['model_prob']), axis=1)
        prob_diff_desc = "(Welo Prob for Winner) - (Model Prob for Winner)"
    else: df['prob_diff'] = 0; prob_diff_desc = "N/A"

    # Add loop strings (loop boolean already calculated)
    intransitive_loops_details = {}
    if len(historical_filtered) > 0:
        for _, target_match in df.iterrows():
            match_idx = target_match['match_index']
            player_A = all_matches_df.loc[match_idx]['A_norm'] if 'A_norm' in all_matches_df.columns else None # Get norm name if needed, handle potential absence
            player_B = all_matches_df.loc[match_idx]['B_norm'] if 'B_norm' in all_matches_df.columns else None
            actual_winner = player_A if all_matches_df.loc[match_idx]['Awin'] == 1 else player_B
            actual_loser  = player_B if all_matches_df.loc[match_idx]['Awin'] == 1 else player_A

            if actual_winner is None or actual_loser is None: continue

            players_C = wins_dict.get(actual_loser, set())
            if not players_C: continue
            loops_for_this_match = []
            for player_C in players_C:
                 if player_C == actual_winner or player_C is None: continue
                 c_wins_over = wins_dict.get(player_C, set())
                 if actual_winner in c_wins_over:
                      loop_str = f"{actual_loser} > {player_C} > {actual_winner}"
                      loops_for_this_match.append(loop_str)
            if loops_for_this_match:
                 intransitive_loops_details[match_idx] = loops_for_this_match

    df['intransitive_loops'] = df['match_index'].apply(lambda idx: "; ".join(intransitive_loops_details.get(idx, [])))

    # Prepare final output DataFrame
    output_df = df[['A_orig', 'B_orig', 'model_prob', 'welo_prob', 'Awin', 'prob_diff', 'involved_in_loop', 'intransitive_loops']].rename(columns={'A_orig': 'A', 'B_orig': 'B'})
    return output_df, prob_diff_desc

# Run and save discrepancy analysis
print("\n--- Running Discrepancy Analysis for CSVs ---")
model_better_output_df, model_prob_diff_desc = analyze_discrepancy(model_better_matches_list, 'model_better')
welo_better_output_df, welo_prob_diff_desc = analyze_discrepancy(welo_better_matches_list, 'welo_better')

# Save CSVs
if model_better_output_df is not None and not model_better_output_df.empty:
    try: model_better_output_df.to_csv(MODEL_BETTER_CSV, index=False); print(f"Model Better analysis results saved to: {MODEL_BETTER_CSV}")
    except Exception as e: print(f"Error saving Model Better CSV: {e}")
if welo_better_output_df is not None and not welo_better_output_df.empty:
    try: welo_better_output_df.to_csv(WELO_BETTER_CSV, index=False); print(f"Welo Better analysis results saved to: {WELO_BETTER_CSV}")
    except Exception as e: print(f"Error saving Welo Better CSV: {e}")


# Keep original Model Better Plot generation
if model_better_output_df is not None and not model_better_output_df.empty:
    print("\n--- Generating Original Model Better Plot ---")
    try:
        plt.figure(figsize=(8, 6))
        sns.boxplot(x='involved_in_loop', y='prob_diff', data=model_better_output_df, palette="coolwarm")
        plt.title('Model Probability Advantage (vs Welo) by Intransitivity Involvement\n(Cases where Model Correct, Welo Incorrect)')
        plt.xlabel('Match Involved in Historical Intransitive Loop (Clay, GS/Masters)')
        plt.ylabel(model_prob_diff_desc)
        plt.xticks([False, True], ['Not Involved', 'Involved'])
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(MODEL_BETTER_PLOT)
        print(f"Model Better visualization saved to: {MODEL_BETTER_PLOT}")
        plt.close()
    except Exception as e: print(f"Error generating Model Better visualization: {e}")

# --- Final Summary Comparison (Keep as before) ---
print("\n--- Overall Intransitivity Loop Involvement Comparison ---")
# ... (rest of the summary comparison logic remains the same) ...
loops_model_better = 0
total_model_better = 0
percent_loops_model_better = 0.0
if model_better_output_df is not None and not model_better_output_df.empty:
    loops_model_better = model_better_output_df['involved_in_loop'].sum()
    total_model_better = len(model_better_output_df)
    percent_loops_model_better = (loops_model_better / total_model_better) * 100 if total_model_better > 0 else 0
    print(f"Model Better Cases: {loops_model_better}/{total_model_better} ({percent_loops_model_better:.1f}%) involved intransitive loops.")
else:
     print("Model Better Cases: No data to analyze.")

loops_welo_better = 0
total_welo_better = 0
percent_loops_welo_better = 0.0
if welo_better_output_df is not None and not welo_better_output_df.empty:
    loops_welo_better = welo_better_output_df['involved_in_loop'].sum()
    total_welo_better = len(welo_better_output_df)
    percent_loops_welo_better = (loops_welo_better / total_welo_better) * 100 if total_welo_better > 0 else 0
    print(f"Welo Better Cases:  {loops_welo_better}/{total_welo_better} ({percent_loops_welo_better:.1f}%) involved intransitive loops.")
else:
     print("Welo Better Cases:  No data to analyze.")


if total_model_better > 0 and total_welo_better > 0: # Check if we have data for both
    if percent_loops_model_better > percent_loops_welo_better:
        print("\nConclusion: A higher percentage of matches where your model correctly predicted (and Welo didn't)")
        print("were involved in historical intransitive loops compared to matches where Welo was correct (and your model wasn't).")
        print("This supports the hypothesis that your model may be better at capturing these complex dynamics.")
    elif percent_loops_model_better == percent_loops_welo_better:
         print("\nConclusion: The percentage of matches involved in historical intransitive loops is the same for both 'Model Better' and 'Welo Better' cases.")
         print("This analysis does not indicate a difference in capturing intransitivity based on this metric.")
    else: # percent_loops_model_better < percent_loops_welo_better
        print("\nConclusion: The percentage of matches involved in historical intransitive loops is lower for")
        print("the 'Model Better' cases compared to the 'Welo Better' cases.")
        print("This analysis does not support the hypothesis that your model's advantage stems from better capturing intransitivity (based on this specific loop definition).")
elif total_model_better > 0:
     print("\nConclusion: Only 'Model Better' cases had data for loop analysis.")
elif total_welo_better > 0:
     print("\nConclusion: Only 'Welo Better' cases had data for loop analysis.")
else:
     print("\nConclusion: No sufficient data for comparison.")


print("\nAnalysis complete.")
