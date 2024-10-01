import os
import csv
import mysql.connector
from datetime import datetime

# MySQL connection details
db_config = {
    'user': 'aicatsan',
    'password': 'aicatsan2024',
    'host': 'localhost',
    'database': 'aicatsan',
}

# Define the folder path where the YYYYMMDD-XXX folders are located
folder_path = '/run/user/1000/gvfs/smb-share:server=192.168.1.155,share=vmimdata/Aicatsan Backup March2023/Y/PSAM'

# Output CSV file
output_file = 'to_process_psam.csv'

# Connect to MySQL
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

# Create and open the output CSV file for writing
with open(output_file, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    
    # Write the header row
    csv_writer.writerow(['video_path', 'session_id', 'subject'])
    
    # Iterate through all folders in the specified folder path
    for folder_name in os.listdir(folder_path):
        # Only process folders with the specified format
        if '-' in folder_name:
            print(folder_name)
            date_part, identifier = folder_name.split('-')[0], folder_name.split('-')[1]
            # Convert date to YYYY-MM-DD format
            folder_date = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
            if datetime.strptime(date_part, '%Y%m%d') < datetime.strptime('20230412', '%Y%m%d'):
                continue
            print(folder_date)
            # Extract the subject id (first two digits) and exercise id (last digit)
            subject = int(identifier[:2])
            exercise_id = 1 if identifier[2] == 'A' else 2
            
            # Construct the Tobii Recording folder path
            tobii_folder = os.path.join(folder_path, folder_name, 'Tobii Recording')
            
            # Find the video file inside the Tobii Recording folder
            video_file = None
            for file in os.listdir(tobii_folder):
                if file.endswith(('.mp4')):  # Adjust based on video file type
                    video_file = os.path.join(tobii_folder, file)
                    break
            
            if video_file:
                # Query the session table to get session_id and subject_id
                query = '''
                    SELECT s.id, s.subject_id, s.exercise_id, su.alias
                    FROM session s
                    JOIN subject su ON s.subject_id = su.id
                    WHERE s.date = %s AND s.client_id = 2 AND s.exercise_id = %s
                '''
                cursor.execute(query, (folder_date, exercise_id))
                results = cursor.fetchall()
                print(results)
                # Process the results based on the smaller and larger subject_id logic
                sessions_by_subject = {}
                for row in results:
                    session_id, subject_id, db_exercise_id, subject_alias = row
                    sessions_by_subject[subject_id] = {'session_id': session_id, 'alias': subject_alias}
                print(sessions_by_subject)
                # Get session IDs for the folder subjects
                if subject == 1:
                    subject_data = sessions_by_subject[(min(sessions_by_subject.keys()))]  # Smaller key 
                elif subject == 2:
                    subject_data = sessions_by_subject[(max(sessions_by_subject.keys()))]  # Smaller key
                print(subject_data)
                # Write the video path and session data to the CSV
                if subject_data:
                    csv_writer.writerow([video_file, subject_data['session_id'], subject_data['alias']])
# Close the cursor and MySQL connection
cursor.close()
connection.close()