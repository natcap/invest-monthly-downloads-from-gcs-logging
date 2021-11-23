.PHONY: download concatenate-usage

# Must be GNU find.
# May need to set this on Windows.
FIND := find
PYTHON := python3

download:
	-mkdir logging
	gsutil -m rsync -r -j "" -x ".*_storage.*" gs://logging-natcap logging

# Grab the header of a file, then grab the contents from all other files.
usage-all.csv:
concatenate-usage:
	$(FIND) logging -name "_usage*" -print -quit | xargs head -n1 > usage-all.csv
	$(FIND) logging -name "_usage*" | xargs grep --no-filename /invest/ >> usage-all.csv

monthly-counts.csv:
	$(PYTHON) monthly-count.py usage-all.csv
