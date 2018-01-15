# LOCDB Log Analysis

## Usage

Either use the **Shorthand**: `sh analyze.sh`
or manually perform the following steps:

1. Apply `prep.vim` to raw logfile from back-end. `:source prep.vim<CR>`
1. Run `python3 analyze.py` on the preprocessed file from the last step.

## To do

Log is already in structured format. Still we need to actually compute the time deltas.

## Important Events

- `REFERENCE SELECTED`
- `COMMIT PRESSED`
