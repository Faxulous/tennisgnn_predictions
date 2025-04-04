This repository is dedicated to publishing ex-ante predictions (with probability estimates) for tennis matches using our graph neural network model.

The model is currently stored in a private repository with commit hash: 0cf9599df962333a3b42bf6b1546816e720b2b4b

This repository will serve as a demonstration of our model, with no possiblity of lookahead-bias, for our forthcoming paper [Tennis match outcome prediction using temporal directed graph neural networks](https://research-information.bris.ac.uk/en/publications/tennis-match-outcome-prediction-using-temporal-directed-graph-neu), available at [11th MathSport International Conference Proceedings 2025](https://math.uni.lu/midas/events/mathsports2025/).

## Tournaments 

The predictions will cover [every match from all Grand Slam and ATP Masters 1000 tournaments held on Clay courts](https://en.wikipedia.org/wiki/2025_ATP_Tour) starting with the Monte-Carlo Masters and ending with the French Open, also known as Roland-Garros:

1. **Monte Carlo Masters (ATP Masters 1000)**: April 6 - April 13, 2025
2. **Madrid Open (ATP Masters 1000)**: April 21 - May 4, 2025
3. **Rome Masters (ATP Masters 1000)**: May 7 - May 18, 2025
4. **Roland Garros (Grand Slam)**: May 25 - June 8, 2025


## Features

- **Match Predictions**: We will provide forecasts for upcoming tennis matches, including probability estimates for each outcome.
- **Live Updates**: New predictions will be published before each tournament round, ensuring no lookahead bias.
- **CSV Format**: Predictions will be saved in the easily accesible CSV format.

## Updates

Updating will be ad-hoc, with probabilities, Kelly stakes, and outcomes updated at different times. Importantly though, our probability estimates will always be published ex-ante. 

Our betting model will be detailed fully in our published work, so we state simply here:

Unit: Bet on the player the model determines as the favourite (probablity>0.5), irrespective of bookmaker odds.
Kelly: Bet on the player the model determines as the favourite (probability>0.5), only if the estimated probalility exceed that of the 1/o, where o is the decimal bookmaker odds for the favourite. 


## Usage

Feel free to access the CSV files to view predictions and track the model's performance over time. As the repository is updated, you will be able to see the latest predictions and accuracy metrics.

Stay tuned for the public release of the model.
