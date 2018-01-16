"""
This script analyzes the contents of a preprocessed (by prep.vim) log file of
the LOC-DB Production System
"""
import fileinput
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta


def event_index(events, key):
    """
    Find's the index of an event. Expects `key` to be either callable to
    evaluate on each event or a (string) value to which the `msg` property of
    the event is compared. The return value -1 means that no match was found.
    """
    if callable(key):
        for i, evnt in enumerate(events):
            if key(evnt):
                return i
    else:
        for i, evnt in enumerate(events):
            if evnt["msg"] == key:
                return i

    return -1


def process_reference(timed_events,
                      key_start='SEARCH ISSUED',
                      key_end='COMMIT PRESSED'):
    """
    Finds the first indices of start_msg and end_msg respectively and
    computes the timespan in between
    """
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
                       sanity_interval=900):
    """
    Filters the reference items for validity, then computes the time span
    for each reference and returns the mean time
    """
    def is_valid(ref):
        """ Returns true, iff entry_group is valid """
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
    try:
        mean = sum(timespans) / len(timespans)
    except TypeError:
        # so people are processing timedelta objects here
        mean = sum(timespans, timedelta(0)) / len(timespans)

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


def eval_count(event_groups,
               criterion,
               name,
               prefix_dir='results'):
    """
    Counts the number of occurences of matching events in each event group
    """
    def satisfies(event):
        if callable(criterion):
            return criterion(event)
        else:
            return event['msg'] == criterion

    counts = [len(list(filter(satisfies, list(zip(*es))[1]))) for es in
              event_groups]

    print("\n## Count Criterion: ", name + "\n")
    print("\n```")
    stats = compute_stats(counts)
    print_stats(*stats)
    print("```\n")
    os.makedirs(prefix_dir, exist_ok=True)
    prefix = os.path.join(prefix_dir, name.lower().replace(' ', '-'))
    print("Writing results to", prefix + '*', file=sys.stderr)
    with open(prefix+'_counts.txt', 'w') as fhandle:
        print(*counts, sep='\n', file=fhandle)
    with open(prefix+'_results.txt', 'w') as fhandle:
        print_stats(*stats, file=fhandle)


def eval_span(event_groups,
              criterion,
              name,
              sanity_interval=None,
              time_unit=None,
              prefix_dir='results'):
    """
    Args
    ====
    event groups : list of list of timed events[[(time, event)]]
    criterion:
    pair of start and end condition (callable, callable) or (str, str)
    name: identifer used for storage and reporting
    """
    key_start, key_end = criterion
    timespans = filter_and_process(event_groups, key_start=key_start,
                                   key_end=key_end,
                                   sanity_interval=sanity_interval)
    if time_unit is not None:
        timespans = [getattr(t, time_unit) for t in timespans]
    print("\n## Span Criterion: ", name + "\n")
    print("Sanity interval: {} seconds.".format(sanity_interval))
    print("\n```")
    stats = compute_stats(timespans)
    print_stats(*stats)
    print("```\n")
    os.makedirs(prefix_dir, exist_ok=True)
    prefix = os.path.join(prefix_dir, name.lower().replace(' ', '-')) \
        + '_' + str(sanity_interval) if sanity_interval is not None else 'ALL'

    print("Writing results to", prefix + '*', file=sys.stderr)
    # write raw seconds file
    with open(prefix+'_seconds.txt', 'w') as fhandle:
        print(*timespans, sep='\n', file=fhandle)
    # write results
    with open(prefix+'_results.txt', 'w') as fhandle:
        print_stats(*stats, file=fhandle)
    try:
        from matplotlib import pyplot as plt
        plt.clf()
        plt.boxplot(timespans)
        plt.savefig(prefix+'_boxplot.png')

        # plt.bar()
        # plt.savefig(prefix+'_histogram.png')
    except ImportError:
        print("[warning] For data visualization, matplotlib is required",
              file=sys.stderr)


def main():
    """ Do all the analysis """
    events_by_entry, __rest = parse_input(fileinput.input())
    event_groups = events_by_entry.values()

    print("# Results\n")

    # Using very first SEARCH ISSUED is more reliable than REFERENCE SELECTED
    eval_span(event_groups,
              ('SEARCH ISSUED', 'COMMIT PRESSED'),
              sanity_interval=300,
              name='linking time', time_unit='seconds')

    def is_internal_suggestion(e):
        """ True iff event corresponds to arrival of internal suggestions """
        return e['msg'] == "SUGGESTIONS ARRIVED" and e['internal']

    def is_external_suggestion(e):
        """ True iff event corresponds to arrival of external suggestions """
        return e['msg'] == "SUGGESTIONS ARRIVED" and not e['internal']

    eval_span(event_groups,
              ('SEARCH ISSUED', is_internal_suggestion),
              sanity_interval=300,
              name='internal suggestion time', time_unit='microseconds')
    eval_span(event_groups,
              ('SEARCH ISSUED', is_external_suggestion),
              sanity_interval=300,
              name='external suggestion time', time_unit='microseconds')

    eval_count(event_groups,
               'SEARCH ISSUED',
               name='number of issued searches')


if __name__ == '__main__':
    main()
