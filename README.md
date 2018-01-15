# LOCDB Log Analysis

## Usage

Either use the **Shorthand**: `sh analyze.sh <log-file>`
or manually perform the following steps:

1. Apply `prep.vim` to raw logfile by opening in in `vim` and issuing `:source
   prep.vim`, then write and quit.
1. Run `python3 analyze.py < <prepocessed-log-file>` to compute all numbers.

## First Results

### Time to resolve a citation link

Based on the time between `SEARCH ISSUED` and `COMMIT PRESSED`.

Mean time for resolving a citation link: Interval: [0:00:09.930000,
0:13:08.654000] with mean value: 0:01:41.307036 based on a sample size of 139
