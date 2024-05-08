import csv
import pandas as pd
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--intervalmarker_path', type=str, required=True)
    parser.add_argument('--exercise_id', type=int, required=True)
    parser.add_argument('--morning_afternoon', choices=['morning','afternoon'], required=True)
    parser.add_argument('--csv_path', type=str, required=True)
    args = parser.parse_args()

    interval_marker = pd.read_csv(args.intervalmarker_path)
    f = open(args.csv_path, 'w')
    writer = csv.writer(f)
    writer.writerow(['demanding_event', 'timestamp_start', 'timestamp_end'])
    
    if args.exercise_id == 1:
        if args.morning_afternoon == 'morning':
            demanding_event = 'steering_failure'
        else:
            demanding_event = 'total_black_out'
        writer.writerow([demanding_event, interval_marker.at[0,'latency'], interval_marker.at[1,'latency']])
    else:
        if args.morning_afternoon == 'morning':
            demanding_events = ['squall', 'tug_failure']
        else:
            demanding_events = ['bow_thruster_failure', 'main_engine_failure']
        writer.writerow([demanding_events[0], interval_marker.at[0,'latency'], interval_marker.at[1,'latency']])
        writer.writerow([demanding_events[1], interval_marker.at[2,'latency'], interval_marker.at[3,'latency']])
    f.close()


