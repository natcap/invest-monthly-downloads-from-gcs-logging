# Scripts for extracting logging from bucket state


## 1. Synchronize state

This will download the raw logs, which at this point is several hundred
thousand files. I've tried to limit the number of files that need to be
downloaded, but it's still a lot.

Grab a cup of coffee and don't do this at home (seriously, run it on a google
cloud VM -- not the cloud console -- and be sure to SSH in properly since it'll
be a lot faster that way than through the web browser).

```
$ make download
```

## 2. Concatenate logging to a single file

This will take the several hundred thousand CSVs downloaded, extract all the
InVEST-related things and copy them to a new CSV that we can parse.

We do this because iterating over many files takes forever, particularly in
python. Joining the needed results into a single file makes the tabulation
much faster.

```
$ make usage-all.csv
```

## 3. Tabulate monthly counts

This will write a single table with mac, windows and total download counts.

```
$ make monthly-counts.csv
```

This is probably what you want to send to the comms team.
