# LOCDB Log Analysis

## Usage

Use either the **shorthand**: `sh analyze.sh <log-file>`
or manually perform the following steps:

1. Apply `prep.vim` to raw logfile by opening in `vim` and issuing `:source
   prep.vim`, then write and quit.
1. Run `python3 analyze.py < <prepocessed-log-file>` to compute all numbers.

## First Results

### Time to Resolve a Citation Link

Based on the time between `SEARCH ISSUED` and `COMMIT PRESSED`. Sanity cut-off at 5 minutes.



#### First evaluation (Jan 2018)

```
N = 444
[Low, High] = [9.93, 557.195]
Quantile@25 = 49.385
Quantile@50 = 89.453
Quantile@75 = 159.185
Mean =  117.99254279279283
```

### Preliminary Results of Second Evaluation (Nov 2018)


```
N = 56
[Low, High] = [3.777, 535.333]
Quantile@25 = 7.79
Quantile@50 = 12.55
Quantile@75 = 21.219
Mean =  29.43166071428572
```


![Violin plot](results/600/linking-time_violinplot2.png)

![Box plot](results/600/linking-time_boxplot.png)

![Histogram](results/600/linking-time_histogram2.png)

For more detailed, and potentially more up-to-date, results check [the results file](results.md) as well as the [results directory](results).
