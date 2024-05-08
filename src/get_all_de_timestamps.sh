echo "Path to folder: $1"
echo "Result folder: $2"

for subject_path in "$1"/* ; do
    subject="$(basename "$subject_path")" 
    echo "Subject: $subject"
    subject_id=${subject:3:${#subject}}
    echo "Subject ID: $subject_id"
    results=`ls "$subject_path"/* | grep -i intervalMarker`
    for result in $results ; do
        echo "$(basename "$result")"
        if [[ "$result" == *"exer1"* ]];then
            echo "$result"
            IFS='_' read -ra IN <<< "$result"
            date=${IN[6]}
            if [ $((subject_id%2)) -eq 0 ];
            then
                echo "File name: ${date:0:4}${date:5:2}${date:8:2}-02A"
                python src/create_de_timestamps_csv.py --intervalmarker_path "$result" --exercise_id 1 --morning_afternoon afternoon --csv_path "$2"/${date:0:4}${date:5:2}${date:8:2}-02A.csv
            else
                echo "File name: ${date:0:4}${date:5:2}${date:8:2}-01A"
                python src/create_de_timestamps_csv.py --intervalmarker_path "$result" --exercise_id 1 --morning_afternoon morning --csv_path "$2"/${date:0:4}${date:5:2}${date:8:2}-01A.csv
            fi
        fi
        if [[ "$result" == *"exer2"* ]];then
            echo "$result"
            IFS='_' read -ra IN <<< "$result"
            date=${IN[6]}
            if [ $((subject_id%2)) -eq 0 ];
            then
                echo "File name: ${date:0:4}${date:5:2}${date:8:2}-02B"
                python src/create_de_timestamps_csv.py --intervalmarker_path "$result" --exercise_id 2 --morning_afternoon afternoon --csv_path "$2"/${date:0:4}${date:5:2}${date:8:2}-02B.csv
            else
                echo "File name: ${date:0:4}${date:5:2}${date:8:2}-01B"
                python src/create_de_timestamps_csv.py --intervalmarker_path "$result" --exercise_id 2 --morning_afternoon morning --csv_path "$2"/${date:0:4}${date:5:2}${date:8:2}-01B.csv
            fi
        fi
    done
done
 