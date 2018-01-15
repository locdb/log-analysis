"""
This script analyzes the contents of a preprocessed (prep.vim) log file of
LOC-DB
"""
import fileinput
import json
from collections import defaultdict
from datetime import datetime, timedelta



def process_reference(events,
                      start_event='SEARCH ISSUED',
                      end_event='COMMIT PRESSED'):
    """ Finds the first indices of start_msg and end_msg respectively and
    computes the timespan in between """
    times, msgs = list(zip(*events))
    start = msgs.index(start_event)
    end = msgs.index(end_event)
    assert start < end, "End event time before start event time"
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
        if (times[end] - times[start]) > timedelta(seconds=sanity_interval):
            # sanity check, maximum seconds for a single citation (defaults to 15 minutes)
            return False
        return True
        
    # First perform validity checks, such that invalid groups do not contribute to mean
    valid_groups = filter(is_valid, entry_groups)

    timespans = [process_reference(g, start_event=start_event, end_event=end_event)
                 for g in valid_groups]

    return len(timespans), (min(timespans), max(timespans)), sum(timespans, timedelta()) / len(timespans)


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
    events_by_entry, __rest = parse_input(fileinput.input())
    event_groups = events_by_entry.values()
    # Using very first SEARCH ISSUED is more reliable than REFERENCE SELECTED
    N, (low, high), mean = filter_and_process(event_groups,
                                              start_event='SEARCH ISSUED',
                                              end_event='COMMIT PRESSED',
                                              sanity_interval=900)
    stats = "Interval: [{}, {}] with mean value: {} based on a sample size of {}"
    print("Mean time for resolving a citation link:", stats.format(low, high, mean, N))




if __name__ == '__main__':
    main()
