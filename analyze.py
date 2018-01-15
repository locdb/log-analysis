""" This script analyzes the contents of a preprocessed (prep.vim) log file of LOC-DB """
import fileinput
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from operator import attrgetter



def process_reference(events,
                      start_event='SEARCH ISSUED',
                      end_event='COMMIT PRESSED'):
    """ Finds the first indices of start_msg and end_msg respectively and
    computes the timespan in between """
    times, msgs = list(zip(*events))
    start = msgs.index(start_event)
    end = msgs.index(end_event)
    assert start < end, "Start event after end event"
    span = times[end] - times[start]
    return span


def filter_and_process(entry_groups,
                       start_event='SEARCH ISSUED',
                       end_event='COMMIT PRESSED',
                       sanity_interval=900,
                       ):
    """ Filters the reference items for validity, then computes the time span
    for each reference and returns the mean time """
    def is_valid(ref):
        times, msgs = list(zip(*ref))
        if start_event not in msgs or end_event not in msgs:
            return False
        start = msgs.index(start_event)
        end = msgs.index(end_event)
        diff = times[end] - times[start]
        if sanity_interval is not None \
                and diff > timedelta(seconds=sanity_interval):
            # sanity check, maximum seconds for a single citation
            # (defaults to 15 minutes)
            return False
        if diff < timedelta():
            # This would be strange, still we need to make sure
            return False
        return True

    # First validity checks, such that invalid groups do not contribute to mean
    valid_groups = filter(is_valid, entry_groups)

    timespans = [process_reference(g, start_event=start_event,
                                   end_event=end_event) for g in valid_groups]

    return timespans


def compute_stats(timespans):
    """ Computes basic statistics of the timespans """
    n_samples = len(timespans)
    interval = (min(timespans), max(timespans))
    mean = sum(timespans) / len(timespans)

    sorted_values = sorted(timespans)
    quantiles = {'25': sorted_values[int(n_samples * .25)],
                 '50': sorted_values[int(n_samples * .50)],
                 '75': sorted_values[int(n_samples * .75)]}

    return n_samples, interval, quantiles, mean


def print_stats(N, interval, quantiles, mean):
    """ Pretty-prints stats such as computed by the function above """
    print("N =", N)
    print("[Low, High] = [{}, {}]".format(*interval))
    for quant, value in quantiles.items():
        print("Quantile@{} = {}".format(quant, value))
    print("Mean = ", mean)


def parse_input(lines):
    """ Groups the lines of the logfile by entry_id and stores (time, event)
    pairs for each reference
    The remainder of events that could not be processed is retained.
    """
    references = defaultdict(list)
    remainder = list()
    for line in lines:
        time_str, json_obj = line.strip().split('\t')

        # parse json object...
        event = json.loads(json_obj)
        # ...and time stamp
        time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        try:
            references[event['entry_id']].append((time, event["msg"]))
        except KeyError:
            # Mostly editing operations
            # print("Missing key in:", event)
            remainder.append((time, event))

    return references, remainder


def main():
    """ Do all the analysis """
    events_by_entry, __rest = parse_input(fileinput.input())
    event_groups = events_by_entry.values()
    # sanity_interval = 900  # 15 minutes
    sanity_interval = 300  # 5 minutes (just two less than 15 minutes)
    # Using very first SEARCH ISSUED is more reliable than REFERENCE SELECTED
    timespans = filter_and_process(event_groups, start_event='SEARCH ISSUED',
                                   end_event='COMMIT PRESSED',
                                   sanity_interval=sanity_interval)

    print("# Time for resolving a citation link")
    seconds = [t.seconds for t in timespans]
    print_stats(*compute_stats(seconds))
    outfile = "tmp/link_resolution_raw_seconds.txt"
    os.makedirs("tmp", exist_ok=True)
    with open(outfile, 'w') as fhandle:
        print("Writing raw seconds to", outfile)
        seconds = map(attrgetter('seconds'), timespans)
        print(*seconds, sep='\n', file=fhandle)

    try:
        from matplotlib import pyplot as plt
        plt.boxplot([t.seconds for t in timespans])
        boxplot_path = "tmp/link_resolution_boxplot.png"
        print("Writing boxplot to", boxplot_path)
        plt.savefig(boxplot_path)
    except ImportError:
        print("For visualization, matplotlib is required")


if __name__ == '__main__':
    main()
