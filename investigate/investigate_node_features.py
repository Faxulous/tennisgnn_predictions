import pandas as pd

# Load the datasets
try:
    preds_df = pd.read_csv('preds.csv')
    # Clean up the 'Awin' column if necessary (remove 'x' if present)
    if preds_df['Awin'].dtype == 'object':
        preds_df['Awin'] = preds_df['Awin'].astype(str).str.replace('x', '', regex=False).str.strip()
        preds_df['Awin'] = pd.to_numeric(preds_df['Awin'], errors='coerce') # Convert to numeric, coerce errors to NaN

    # Drop rows where Awin is NaN after cleaning
    preds_df.dropna(subset=['Awin'], inplace=True)
    preds_df['Awin'] = preds_df['Awin'].astype(int) # Convert Awin to integer

    men_df = pd.read_csv('men.csv')
except FileNotFoundError:
    print("Error: 'preds.csv' or 'men.csv' not found. Please ensure the files are in the correct directory.")
    exit()
except Exception as e:
    print(f"An error occurred while loading the data: {e}")
    exit()


model_better = []
welo_better = []

# Iterate through the predictions
for index, row in preds_df.iterrows():
    model_prob = row['model_prob']
    welo_prob = row['welo_prob']
    awin = row['Awin']
    player_a = row['A']
    player_b = row['B']

    # Determine correctness
    model_correct = (model_prob > 0.5 and awin == 1) or (model_prob < 0.5 and awin == 0)
    welo_correct = (welo_prob > 0.5 and awin == 1) or (welo_prob < 0.5 and awin == 0)

    # Check for discrepancies
    if model_correct and not welo_correct:
        model_better.append({
            'A': player_a,
            'B': player_b,
            'model_prob': model_prob,
            'welo_prob': welo_prob,
            'Awin': awin
        })
    elif not model_correct and welo_correct:
         welo_better.append({
            'A': player_a,
            'B': player_b,
            'model_prob': model_prob,
            'welo_prob': welo_prob,
            'Awin': awin
        })

print("Matches where model_prob was correct and welo_prob was incorrect:")
if model_better:
    model_better_df = pd.DataFrame(model_better)
    print(model_better_df)
    print(f"\nTotal count: {len(model_better_df)}")
else:
    print("None")


print("\nMatches where welo_prob was correct and model_prob was incorrect:")
if welo_better:
    welo_better_df = pd.DataFrame(welo_better)
    print(welo_better_df)
    print(f"\nTotal count: {len(welo_better_df)}")

else:
    print("None")

# --- Further analysis with player characteristics ---

# Sets to store names of players not found
model_better_not_found = set()
welo_better_not_found = set()


def get_player_chars(player_name):
    """Fetches characteristics for a player from men_df."""
    # Attempt to match player name variations
    # Basic match:
    player_data = men_df[men_df['player_name'] == player_name]
    if not player_data.empty:
        # Check if height or righthanded is missing in the found row
        if pd.isna(player_data.iloc[0]['height']) or pd.isna(player_data.iloc[0]['righthanded']):
             # print(f"Info: Found player '{player_name}' but missing height/handedness.")
             return pd.Series({'height': None, 'righthanded': None}) # Treat as not found for analysis
        return player_data.iloc[0][['height', 'righthanded']]

    # Try matching last name and first initial if basic match fails
    parts = player_name.split('.') # Assuming format "Lastname F."
    if len(parts) == 2:
         # Handle cases like "J.L." or "C. H." for initials
        last_name = parts[0].strip()
        first_initial = parts[1].strip()
        # Search for players with the same last name
        potential_matches = men_df[men_df['player_name'].str.startswith(last_name + ' ')]
        if not potential_matches.empty:
             # Check if first initial matches
            for _, p_row in potential_matches.iterrows():
                 name_parts = p_row['player_name'].split(' ')
                 if len(name_parts) > 1 and name_parts[1].startswith(first_initial):
                    if pd.isna(p_row['height']) or pd.isna(p_row['righthanded']):
                        # print(f"Info: Found player '{player_name}' (as {p_row['player_name']}) but missing height/handedness.")
                        return pd.Series({'height': None, 'righthanded': None})
                    return p_row[['height', 'righthanded']]


    # Try matching "Lastname F" without the dot
    parts_no_dot = player_name.replace('.', '').split(' ')
    if len(parts_no_dot) >= 2:
        last_name = parts_no_dot[0].strip()
        first_initial = parts_no_dot[1].strip()
        # Search for players with the same last name
        potential_matches = men_df[men_df['player_name'].str.startswith(last_name + ' ')]
        if not potential_matches.empty:
             # Check if first initial matches
            for _, p_row in potential_matches.iterrows():
                 name_parts = p_row['player_name'].split(' ')
                 if len(name_parts) > 1 and name_parts[1].startswith(first_initial):
                    if pd.isna(p_row['height']) or pd.isna(p_row['righthanded']):
                        # print(f"Info: Found player '{player_name}' (as {p_row['player_name']}) but missing height/handedness.")
                        return pd.Series({'height': None, 'righthanded': None})
                    return p_row[['height', 'righthanded']]

    # If not found by any method
    # print(f"Warning: Player '{player_name}' not found or has ambiguous match in men.csv")
    return pd.Series({'height': None, 'righthanded': None})


print("\n--- Analysis of Player Characteristics ---")

# Analyze Model Better Cases
if model_better:
    print("\nCharacteristics analysis for matches where model_prob performed better:")
    characteristics = []
    current_model_better_not_found = set() # Track for this specific analysis run
    for match in model_better:
        player_a_chars = get_player_chars(match['A'])
        player_b_chars = get_player_chars(match['B'])

        # Track not found players
        if player_a_chars['height'] is None or player_a_chars['righthanded'] is None:
            current_model_better_not_found.add(match['A'])
        if player_b_chars['height'] is None or player_b_chars['righthanded'] is None:
            current_model_better_not_found.add(match['B'])

        characteristics.append({
            'A': match['A'],
            'B': match['B'],
            'A_height': player_a_chars['height'],
            'A_righthanded': player_a_chars['righthanded'],
            'B_height': player_b_chars['height'],
            'B_righthanded': player_b_chars['righthanded'],
            'Awin': match['Awin']
        })
    model_better_chars_df = pd.DataFrame(characteristics)
    model_better_not_found.update(current_model_better_not_found) # Add to overall set

    # Display summary statistics or patterns (e.g., height difference, handedness matchup)
    # Calculate height difference (handle potential NaNs)
    model_better_chars_df['height_diff'] = pd.to_numeric(model_better_chars_df['A_height'], errors='coerce') - pd.to_numeric(model_better_chars_df['B_height'], errors='coerce')

    # Calculate handedness matchup (R vs L, R vs R, L vs L, L vs R) - handle NaNs
    def get_handedness_matchup(row):
        rh_a = row['A_righthanded']
        rh_b = row['B_righthanded']
        if pd.isna(rh_a) or pd.isna(rh_b):
            return 'Unknown'
        rh_a = int(rh_a)
        rh_b = int(rh_b)
        if rh_a == 1 and rh_b == 0: return 'R_vs_L'
        if rh_a == 1 and rh_b == 1: return 'R_vs_R'
        if rh_a == 0 and rh_b == 0: return 'L_vs_L'
        if rh_a == 0 and rh_b == 1: return 'L_vs_R'
        return 'Unknown' # Should not happen if data is clean 0 or 1

    model_better_chars_df['handedness_matchup'] = model_better_chars_df.apply(get_handedness_matchup, axis=1)

    print("\nHeight Difference Summary (Model Better):")
    print(model_better_chars_df['height_diff'].describe())

    print("\nHandedness Matchup Counts (Model Better):")
    print(model_better_chars_df['handedness_matchup'].value_counts())


# Analyze Welo Better Cases
if welo_better:
    print("\nCharacteristics analysis for matches where welo_prob performed better:")
    characteristics = []
    current_welo_better_not_found = set() # Track for this specific analysis run
    for match in welo_better:
        player_a_chars = get_player_chars(match['A'])
        player_b_chars = get_player_chars(match['B'])

        # Track not found players
        if player_a_chars['height'] is None or player_a_chars['righthanded'] is None:
            current_welo_better_not_found.add(match['A'])
        if player_b_chars['height'] is None or player_b_chars['righthanded'] is None:
            current_welo_better_not_found.add(match['B'])

        characteristics.append({
            'A': match['A'],
            'B': match['B'],
            'A_height': player_a_chars['height'],
            'A_righthanded': player_a_chars['righthanded'],
            'B_height': player_b_chars['height'],
            'B_righthanded': player_b_chars['righthanded'],
            'Awin': match['Awin']
        })
    welo_better_chars_df = pd.DataFrame(characteristics)
    welo_better_not_found.update(current_welo_better_not_found) # Add to overall set

    welo_better_chars_df['height_diff'] = pd.to_numeric(welo_better_chars_df['A_height'], errors='coerce') - pd.to_numeric(welo_better_chars_df['B_height'], errors='coerce')
    welo_better_chars_df['handedness_matchup'] = welo_better_chars_df.apply(get_handedness_matchup, axis=1)


    print("\nHeight Difference Summary (Welo Better):")
    print(welo_better_chars_df['height_diff'].describe())

    print("\nHandedness Matchup Counts (Welo Better):")
    print(welo_better_chars_df['handedness_matchup'].value_counts())


# Print the names of players not found or with missing data
print("\n--- Players Not Found or Missing Data ---")
print("\nPlayers involved in 'Model Better' cases but not found/matched in men.csv:")
if model_better_not_found:
    for name in sorted(list(model_better_not_found)):
        print(f"- {name}")
else:
    print("None found.")

print("\nPlayers involved in 'Welo Better' cases but not found/matched in men.csv:")
if welo_better_not_found:
    for name in sorted(list(welo_better_not_found)):
        print(f"- {name}")
else:
    print("None found.")

