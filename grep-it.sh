for year in {2019..2020}
do
        for month in {1..12}
        do
                echo "$year-$month $(grep -v data summary.txt | grep $year-$month- | wc -l)"
        done
done
