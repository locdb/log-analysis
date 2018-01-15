"""
This script analyzes the contents of a preprocessed (prep.vim) log file of
LOC-DB
"""
import fileinput
import json
from collections import defaultdict
from datetime import datetime


def process_reference(events):
    for time, msg in events:
        print(time, msg)



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
    references, __rest = parse_input(fileinput.input())
    list(map(process_reference, references.values()))






if __name__ == '__main__':
    main()
