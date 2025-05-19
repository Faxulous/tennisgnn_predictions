import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.spatial.distance import jensenshannon

def brier_score(y_true, y_prob):
    return np.mean((y_true - y_prob) ** 2)

def kelly_stake(prob, odds):
    # Kelly formula: f* = (bp - q)/b, where b=odds-1, p=prob, q=1-p
    b = odds - 1
    return np.clip((prob * b - (1 - prob)) / b, 0, 1) if b > 0 else 0

def js_divergence(p, q):
    # p, q: arrays of probabilities for class 1 (A win)
    # Convert to distributions over [A win, B win]
    p = np.vstack([p, 1 - p]).T
    q = np.vstack([q, 1 - q]).T
    # Compute JS divergence for each row, then mean
    return np.mean([jensenshannon(pi, qi, base=2)**2 for pi, qi in zip(p, q)])

def evaluate(df, prob_col, odds_col, y_col='Awin'):
    # Classification accuracy
    acc = accuracy_score(df[y_col], (df[prob_col] > 0.5).astype(int))
    # Brier score
    brier = brier_score(df[y_col], df[prob_col])
    # ROI: unit bet on favourite
    roi_unit = []
    for _, row in df.iterrows():
        fav = row[prob_col] > 0.5
        if fav:
            odds = row[odds_col]
            win = row[y_col] == 1
        else:
            odds = row['PSB'] if odds_col == 'PSA' else np.nan
            win = row[y_col] == 0
        if np.isnan(odds):
            roi_unit.append(0)
        else:
            roi_unit.append((odds - 1) if win else -1)
    roi_unit = np.mean(roi_unit)
    # ROI: Kelly, bankroll reset to 1 each bet
    roi_kelly = []
    for _, row in df.iterrows():
        fav = row[prob_col] > 0.5
        if fav:
            odds = row[odds_col]
            prob = row[prob_col]
            win = row[y_col] == 1
        else:
            odds = row['PSB'] if odds_col == 'PSA' else np.nan
            prob = 1 - row[prob_col]
            win = row[y_col] == 0
        if np.isnan(odds):
            roi_kelly.append(0)
        else:
            stake = kelly_stake(prob, odds)
            roi_kelly.append(stake * (odds - 1) if win else -stake)
    roi_kelly = np.mean(roi_kelly)
    # Jensen-Shannon divergence to odds-implied probability (ps_prob)
    jsd = js_divergence(df[prob_col].values, df['ps_prob'].values)
    return acc, brier, roi_unit, roi_kelly, jsd

df = pd.read_csv('preds.csv')
# Only keep rows with all required columns
for col in ['Awin','PSA','PSB','ps_prob','model_prob','welo_prob','bt_prob']:
    df = df[df[col].notnull()]
    if col != 'Awin':
        df = df[df[col] != '']

eval_cols = [
    ('ps_prob', 'PSA'),
    ('model_prob', 'PSA'),
    ('welo_prob', 'PSA'),
    ('bt_prob', 'PSA'),
]

for prob_col, odds_col in eval_cols:
    acc, brier, roi_unit, roi_kelly, jsd = evaluate(df, prob_col, odds_col)
    print(f"{prob_col}: Accuracy={acc:.3f}, Brier={brier:.3f}, ROI_unit={roi_unit:.3f}, ROI_kelly={roi_kelly:.3f}, JS_div(ps_prob)={jsd:.4f}")

# Plot PnL over time for model_prob
unit_pnl = [0]
kelly_pnl = [0]
unit_cum = 0
kelly_cum = 0
for _, row in df.iterrows():
    fav = row['model_prob'] > 0.5
    if fav:
        odds = row['PSA']
        win = row['Awin'] == 1
        prob = row['model_prob']
    else:
        odds = row['PSB']
        win = row['Awin'] == 0
        prob = 1 - row['model_prob']
    # Unit bet
    if np.isnan(odds):
        unit_cum += 0
    else:
        unit_cum += (odds - 1) if win else -1
    unit_pnl.append(unit_cum)
    # Kelly bet
    if np.isnan(odds):
        kelly_cum += 0
    else:
        stake = kelly_stake(prob, odds)
        kelly_cum += stake * (odds - 1) if win else -stake
    kelly_pnl.append(kelly_cum)

plt.figure(figsize=(10,6))
plt.plot(unit_pnl, label='Unit Bet PnL (model_prob)')
plt.plot(kelly_pnl, label='Kelly PnL (model_prob)')
plt.xlabel('Bet Number')
plt.ylabel('Cumulative PnL')
plt.title('Cumulative PnL over Time (model_prob)')
plt.legend()
plt.tight_layout()
# Add gridlines for both axes
ax = plt.gca()
ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=30, integer=True))
plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)
plt.show() 