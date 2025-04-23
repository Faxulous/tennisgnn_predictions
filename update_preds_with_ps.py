import pandas as pd
from shin import calculate_implied_probabilities
# Read tennisdata.csv and create both (A,B) and (B,A) orderings
raw = pd.read_csv('tennisdata.csv')

# (A=winner, B=loser)
ab = raw.rename(columns={'W': 'A', 'L': 'B', 'PSW': 'PSA', 'PSL': 'PSB'})
ab['Awin'] = 1
# (A=loser, B=winner)
ba = raw.rename(columns={'W': 'B', 'L': 'A', 'PSW': 'PSB', 'PSL': 'PSA'})
ba['Awin'] = 0

# Combine both orderings
data = pd.concat([ab[['A','B','Awin','PSA','PSB']], ba[['A','B','Awin','PSA','PSB']]], ignore_index=True)

# Calculate ps_prob using Shin's method
ps_probs = []
for _, row in data.iterrows():
    try:
        psa, psb = float(row['PSA']), float(row['PSB'])
        ps_prob = calculate_implied_probabilities([psa, psb])[0]
    except Exception:
        ps_prob = None
    ps_probs.append(ps_prob)
data['ps_prob'] = ps_probs

# Read preds.csv
preds = pd.read_csv('preds.csv')

# Merge, updating Awin, PSA, PSB, ps_prob
preds_updated = preds.drop(['Awin','PSA','PSB','ps_prob'], axis=1, errors='ignore').merge(
    data, on=['A','B'], how='left')

# Save
preds_updated.to_csv('preds.csv', index=False)
print('Updated preds saved to preds.csv') 