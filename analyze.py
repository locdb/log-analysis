""" This script analyzes the contents of a preprocessed (prep.vim) log file of LOC-DB """
import fileinput
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from operator import attrgetter



def event_index(events, key):
    if callable(key):
        for i, e in enumerate(events):
            if key(e):
                return i
    else:
        for i, e in enumerate(events):
            if e["msg"] == key:
                return i

    return -1

def process_reference(timed_events,
                      key_start='SEARCH ISSUED',
                      key_end='COMMIT PRESSED',
                      ):
    """ Finds the first indices of start_msg and end_msg respectively and
    computes the timespan in between """
    times, events = list(zip(*timed_events))

    # start = msgs.index(start_event)
    # end = msgs.index(end_event)
    start = event_index(events, key_start)
    end = event_index(events, key_end)
    assert start < end, "Start event after end event"

    span = times[end] - times[start]

    return span


def filter_and_process(entry_groups,
                       key_start='SEARCH ISSUED',
                       key_end='COMMIT PRESSED',
                       sanity_interval=900,
                       ):
    """ Filters the reference items for validity, then computes the time span
    for each reference and returns the mean time """
    def is_valid(ref):
        times, events = list(zip(*ref))
        start = event_index(events, key_start)
        end = event_index(events, key_end)
        if start == -1 or end == -1:
            # not present inside record
            return False
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

    timespans = [process_reference(g, key_start=key_start,
                                   key_end=key_end) for g in valid_groups]

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


def print_stats(N, interval, quantiles, mean, file=sys.stdout):
    """ Pretty-prints stats such as computed by the function above """
    print("N =", N, file=file)
    print("[Low, High] = [{}, {}]".format(*interval), file=file)
    for quant, value in quantiles.items():
        print("Quantile@{} = {}".format(quant, value), file=file)
    print("Mean = ", mean, file=file)


def parse_input(lines):
    """ Groups the lines of the logfile by entry_id and stores (time, event)
    pairs for each reference
    The remainder of events that could not be processed is retained.
    """
    events_by_entry = defaultdict(list)
    remainder = list()
    for line in lines:
        time_str, json_obj = line.strip().split('\t')

        # parse json object...
        event = json.loads(json_obj)
        # ...and time stamp
        time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        try:
            entry_id = event.pop('entry_id')
            events_by_entry[entry_id].append((time, event))
        except KeyError:
            # Mostly editing operations
            # print("Missing key in:", event)
            remainder.append((time, event))

    return events_by_entry, remainder



def eval_criterion(event_groups, criterion, name, sanity_interval=None, prefix_dir='results'):
    """
    Args
    ====
    event groups : list of list of timed events[[(time, event)]]
    criterion: pair of start and end condition (callable, callable) or (str, str)
    name: identifer used for storage and reporting
    """
    key_start, key_end = criterion
    timespans = filter_and_process(event_groups, key_start=key_start,
                                   key_end=key_end,
                                   sanity_interval=sanity_interval)
    seconds = [t.seconds for t in timespans]
    print("# Criterion: ", name)
    print_stats(*compute_stats(seconds))
    os.makedirs(prefix_dir, exist_ok=True)
    prefix = os.path.join(prefix_dir, name.lower().replace(' ', '-')) \
        + '_' + str(sanity_interval) if sanity_interval is not None else 'ALL'

    print("Writing results to", prefix + '*')
    # write raw seconds file
    with open(prefix+'_seconds.txt', 'w') as fhandle:
        print(*seconds, sep='\n', file=fhandle)
    # write results
    with open(prefix+'_results.txt', 'w') as fhandle:
        print_stats(*compute_stats(seconds), file=fhandle)
    try:
        from matplotlib import pyplot as plt
        plt.boxplot(seconds)
        plt.savefig(prefix+'_boxplot.png')

        # plt.bar()
        # plt.savefig(prefix+'_histogram.png')
    except ImportError:
        print("For visualization, matplotlib is required")
    print("Done.")

    # write box plot


def main():
    """ Do all the analysis """
    events_by_entry, __rest = parse_input(fileinput.input())
    event_groups = events_by_entry.values()
    # sanity_interval = 900  # 15 minutes
    sanity_interval = 300  # 5 minutes (just two less than 15 minutes)
    # Using very first SEARCH ISSUED is more reliable than REFERENCE SELECTED

    eval_criterion(event_groups, ('SEARCH ISSUED', 'COMMIT PRESSED'), sanity_interval=300, name='linking time')

    def is_internal_suggestion(e):
        return e['msg'] == "SUGGESTIONS ARRIVED" and e['internal']
    def is_external_suggestion(e):
        return e['msg'] == "SUGGESTIONS ARRIVED" and not e['internal']

    eval_criterion(event_groups, ('SEARCH ISSUED',is_internal_suggestion), sanity_interval=300, name='internal sug time')
    eval_criterion(event_groups, ('SEARCH ISSUED',is_external_suggestion), sanity_interval=300, name='external sug time')



if __name__ == '__main__':
    main()
