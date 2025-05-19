import pandas as pd
from collections import Counter

# Load the CSV data into a DataFrame
file_path = 'preds.csv'
data = pd.read_csv(file_path)

# Determine correct classifications
welo_correct = (data['welo_prob'] > 0.5) == (data['Awin'] == 1)
bt_correct = (data['bt_prob'] > 0.5) == (data['Awin'] == 1)
ps_correct = (data['ps_prob'] > 0.5) == (data['Awin'] == 1)
model_wrong = (data['model_prob'] > 0.5) != (data['Awin'] == 1)

# Filter rows where welo, bt, and ps were correct, and model was wrong
filtered_rows = data[welo_correct & bt_correct & ps_correct & model_wrong]

# Count the most common players in columns A and B
players = filtered_rows['A'].tolist() + filtered_rows['B'].tolist()
player_counts = Counter(players)

# Get the 10 most common players
most_common_players = player_counts.most_common(10)

# Print the most common players
print("Most common players in these matches:")
for player, count in most_common_players:
    print(f"{player}: {count}") 