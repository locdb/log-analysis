import sys
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import codecs

def find_nearest(array,value):
    idx = (np.abs(array - value)).argmin()
    return idx

def plot(numbers):
    sns.set()
    with sns.plotting_context("paper"):
        x = np.arange(len(numbers))
        median = np.median(numbers)
        idx_median = find_nearest(numbers, median)
        min = np.min(numbers)
        idx_min = 0
        max = np.max(numbers)
        idx_max = len(numbers)-1

        q1 = np.percentile(numbers, 25)
        idx_q1 = find_nearest(numbers, q1)
        q3 = np.percentile(numbers, 75)
        idx_q3 = find_nearest(numbers, q3)

        # as a sanity check
        print("Median: " + str(median))
        print("Min: " + str(min))
        print("Max: " + str(max))
        print("Q1: " + str(q1))
        print("Q3: " + str(q3))

        plt.clf()
        plt.ylabel("seconds")
        plt.xlabel("ordered experiments for reference linking")
        plt.scatter(x=x, y=numbers, marker="+")#s=1.5)

        plt.scatter(x=idx_median, y=median, marker="x", color=sns.color_palette()[1])
        plt.text(idx_median, median-20, "median=" + str(median),ha='left', va='top')

        plt.scatter(x=idx_min, y=min, marker="x", color=sns.color_palette()[1])
        plt.text(idx_min, min, "min=" + str(min),ha='left', va='top')
        plt.scatter(x=idx_max, y=max, marker="x", color=sns.color_palette()[1])
        plt.text(idx_max, max, "max=" + str(max), ha='right', va='bottom')

        plt.scatter(x=idx_q1, y=q1, marker="x", color=sns.color_palette()[1])
        plt.text(idx_q1, q1-20, "q1=" + str(q1),ha='left', va='top')
        plt.scatter(x=idx_q3, y=q3, marker="x", color=sns.color_palette()[1])
        plt.text(idx_q3, q3, "q3=" + str(q3), ha='right', va='bottom')

        #plt.savefig('scatter.pdf', bbox_inches='tight')
        plt.show()


def main():
    print("Process started")
    data = []
    with codecs.open("./data.txt") as f:
        for line in f.readlines():
            data.append(float(line))
    plot(np.array(data))

if __name__=="__main__":
    main()