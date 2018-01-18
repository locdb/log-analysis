"""
This script analyzes the contents of a preprocessed (by prep.vim) log file of
the LOC-DB Production System
"""
import fileinput
import json
import os
import sys
from collections import defaultdict, Counter
from operator import itemgetter
from datetime import datetime, timedelta


def event_index(events, key, start=0):
    """
    Find's the index of an event. Expects `key` to be either callable to
    evaluate on each event or a (string) value to which the `msg` property of
    the event is compared. The return value -1 means that no match was found.
    """
    for i in range(start, len(events)):
        event = events[i]
        if callable(key):
            if key(event):
                return i
        else:
            try:
                if event["msg"] == key:
                    return i
            except KeyError:
                pass
    # for loop exceeded without return statement
    raise ValueError


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


def paired_times(timed_events, criterion):
    """
    Given a list of timed events, find multiple timedeltas matching criterion.
    Does not check, whether the end event actually fits to the start event
    (e.g. having same resource id), this can be done via grouping before.
    """
    key_start, key_end = criterion
    times, events = zip(*timed_events)
    captured_times = []
    current = 0
    while current < len(events):
        try:
            start = event_index(events, key_start, current)
            end = event_index(events, key_end, start + 1)
            diff = times[end] - times[start]
            assert diff > timedelta(0), "Something went terribly wrong"
            captured_times.append(diff)
            current = end + 1
        except ValueError:
            # events_index returned 'not found'
            break
    return captured_times


def filter_groups(entry_groups,
                  criterion=('SEARCH ISSUED', 'COMMIT PRESSED'),
                  should_contain=[],
                  sanity_interval=None):
    """
    Filters the reference items for validity, then computes the time span
    for each reference and returns the mean time
    """
    key_start, key_end = criterion

    def is_valid(ref):
        """ Returns true, iff entry_group is valid """
        times, events = list(zip(*ref))
        try:
            start = event_index(events, key_start)
            end = event_index(events, key_end)
            for key in should_contain:
                # will raise ValueError, when not contained
                event_index(events, key)
        except ValueError:
            return False
        diff = times[end] - times[start]
        if sanity_interval is not None \
                and diff > timedelta(seconds=sanity_interval):
            # sanity check, maximum seconds for a single citation
            # (defaults to 15 minutes)
            return False
        if diff < timedelta():
            # This would be strange, still we need to make sure
            raise UserWarning("End event before start event")
        return True

    # First validity checks, such that invalid groups do not contribute to mean
    valid_groups = filter(is_valid, entry_groups)
    return list(valid_groups)


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


def print_stats(n_samples, interval, quantiles, mean, file=sys.stdout):
    """ Pretty-prints stats such as computed by the function above """
    print("N =", n_samples, file=file)
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
        """ Returns True iff criterion is satisfied (either funct or str) """
        # if callable(criterion):
        #     return criterion(event)
        # return event['msg'] == criterion
        return criterion(event) if callable(criterion) \
                else event['msg'] == criterion

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
    with open(prefix+'_distribution.txt', 'w') as fhandle:
        print(*sorted(Counter(counts).items(), key=itemgetter(0)), sep='\n',
              file=fhandle)
    with open(prefix+'_counts.txt', 'w') as fhandle:
        print(*counts, sep='\n', file=fhandle)
    with open(prefix+'_results.txt', 'w') as fhandle:
        print_stats(*stats, file=fhandle)


def plot_box_hist(numbers, prefix):
    """ Draw and save boxplot and histogram for `numbers`,
    filenames are generated by appending to `prefix` """
    try:
        from matplotlib import pyplot as plt
        plt.figure(figsize=(32, 16))
        plt.clf()
        plt.ylabel("seconds")
        plt.boxplot(numbers)
        plt.savefig(prefix+'_boxplot.png')

        plt.clf()
        plt.ylabel("amount")
        plt.xlabel("seconds")
        plt.hist(numbers, color='b')
        plt.savefig(prefix+'_histogram.png')

        plt.clf()
        plt.ylabel("amount")
        plt.xlabel("seconds")
        plt.xticks([0, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600])
        plt.hist(numbers, [0, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600],
                 color='royalblue', align='mid', rwidth=.5)
        plt.savefig(prefix+'_histogram1.pdf')

        plt.clf()
        plt.xlabel("seconds")
        # plt.yticks(["citation linking"])
        plt.violinplot(numbers, showmeans=True, showmedians=True, vert=False)
        plt.savefig(prefix+'_violinplot.png')
    except ImportError:
        print("[warning] For data visualization, matplotlib is required",
              file=sys.stderr)


def eval_span(event_groups,
              criterion,
              name,
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
    timespans = [process_reference(g, key_start=key_start,
                                   key_end=key_end) for g in event_groups]
    # timespans = filter_and_process(event_groups,
    #                                key_start=key_start,
    #                                key_end=key_end,
    #                                sanity_interval=sanity_interval)
    timespans = [t.total_seconds() for t in timespans]
    print("\n## Span Criterion: ", name + "\n")
    print("\n```")
    stats = compute_stats(timespans)
    print_stats(*stats)
    print("```\n")
    os.makedirs(prefix_dir, exist_ok=True)
    prefix = os.path.join(prefix_dir, name.lower().replace(' ', '-'))

    print("Writing results to", prefix + '*', file=sys.stderr)
    # write raw seconds file
    with open(prefix + '_seconds.txt', 'w') as fhandle:
        print(*timespans, sep='\n', file=fhandle)
    # write results
    with open(prefix+'_results.txt', 'w') as fhandle:
        print_stats(*stats, file=fhandle)
    plot_box_hist(timespans, prefix)


def eval_multi_spans(events, criterion, name, sanity_interval=None,
                     prefix_dir='results'):
    """
    Given a list of timed events [(time, event)] find paired events that match
    criterion and compute basic statistics plus draw plots.
    """
    timespans = paired_times(events, criterion)
    timespans = [t.total_seconds() for t in timespans]
    if sanity_interval:
        timespans = [t for t in timespans if t < sanity_interval]
    print("\n## Multi-Span Criterion: ", name + "\n")
    print("Sanity interval: {} seconds.".format(sanity_interval))
    print("\n```")
    stats = compute_stats(timespans)
    print_stats(*stats)
    print("```\n")
    os.makedirs(prefix_dir, exist_ok=True)
    prefix = os.path.join(prefix_dir, name.lower().replace(' ', '-'))

    print("Writing results to", prefix + '*', file=sys.stderr)
    # write raw seconds file
    with open(prefix + '_seconds.txt', 'w') as fhandle:
        print(*timespans, sep='\n', file=fhandle)
    # write results
    with open(prefix+'_results.txt', 'w') as fhandle:
        print_stats(*stats, file=fhandle)
    plot_box_hist(timespans, prefix)


def main():
    """ Do all the analysis """
    events_by_entry, ungrouped_events = parse_input(fileinput.input())
    event_groups = events_by_entry.values()
    sanity_interval = 600

    def is_internal_suggestion(evnt):
        """ True iff event corresponds to arrival of internal suggestions """
        return evnt['msg'] == "SUGGESTIONS ARRIVED" and evnt['internal']

    def is_external_suggestion(evnt):
        """ True iff event corresponds to arrival of external suggestions """
        return evnt['msg'] == "SUGGESTIONS ARRIVED" and not evnt['internal']

    valid_groups = filter_groups(event_groups,
                                 ("SEARCH ISSUED", "COMMIT PRESSED"),
                                 should_contain=[is_internal_suggestion, is_external_suggestion],
                                 sanity_interval=sanity_interval)

    print("# Results\n")

    print("Sanity interval", sanity_interval)

    print("Inspected groups = ", len(event_groups))
    print("Valid groups = ", len(valid_groups))
    print("Link resolved within sanity interval and contain both internal and external suggestions")

    out_dir = os.path.join('results', str(sanity_interval) if sanity_interval
                           else 'ALL')
    # Using very first SEARCH ISSUED is more reliable than REFERENCE SELECTED
    eval_span(valid_groups,
              ('SEARCH ISSUED', 'COMMIT PRESSED'),
              name='linking time',
              prefix_dir=out_dir)

    eval_span(valid_groups,
              ('SEARCH ISSUED', is_internal_suggestion),
              name='internal suggestion time',
              prefix_dir=out_dir)
    eval_span(valid_groups,
              ('SEARCH ISSUED', is_external_suggestion),
              name='external suggestion time',
              prefix_dir=out_dir)

    eval_count(valid_groups,
               'SEARCH ISSUED',
               name='number of issued searches',
               prefix_dir=out_dir)

    eval_multi_spans(ungrouped_events, ('START EDITING', 'STOP EDITING'),
                     sanity_interval=sanity_interval,
                     name='editing time',
                     prefix_dir=out_dir)


if __name__ == '__main__':
    main()
