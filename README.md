# LOCDB Log Analysis

## Usage

Either use the **Shorthand**: `sh analyze.sh <log-file>`
or manually perform the following steps:

1. Apply `prep.vim` to raw logfile by opening in in `vim` and issuing `:source prep.vim`, then write and quit.
1. Run `python3 analyze.py < <prepocessed-log-file>` to compute all numbers.

## To do

Log is already in structured format. Still we need to actually compute the time deltas.

## Important Events

- `REFERENCE SELECTED`
- `COMMIT PRESSED`
