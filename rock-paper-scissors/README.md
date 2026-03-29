# Rock Paper Scissors

Simple browser game built in a single file (`index.html`) with persistent score tracking.

## Run
1. Open `index.html` in any browser.
2. Click `Rock`, `Paper`, or `Scissors` to play rounds.

## How it works
- `playRound(choice)` picks a random computer move and gets result via `getOutcome(player, computer)`.
- Result updates state counters: `wins`, `losses`, `ties`, `rounds`.
- UI is refreshed by `renderScore()` and `renderResult(...)`.
- Scores are saved to `localStorage` under key `rps-score-v1` with `saveScore()`.
- On load, `loadScore()` restores saved values (or defaults to zeros).
- `Reset Score` sets all counters to `0` and overwrites saved data.
