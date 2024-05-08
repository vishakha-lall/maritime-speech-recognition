echo "Path to video folder: $1"
echo "Path to csv folder: $2"
echo "Path to result folder: $3"

for subject_path in "$1"/* ; do
    subject="$(basename "$subject_path")" 
    echo $subject
    video_path="$subject_path/Tobii Recording/rendered.mp4"
    csv_path="$2/$subject.csv"
    if test -f $csv_path; then
        python src/init.py --video_path "$video_path" --csv_path "$csv_path" --loglevel DEBUG --results_path "$3" --subject_id "$subject"
    fi
done