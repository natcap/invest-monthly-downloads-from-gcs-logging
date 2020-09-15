.PHONY: download concatenate-usage

# Must be GNU find.
# May need to set this on Windows.
FIND := find

download:
	-mkdir logging
	gsutil -m rsync -r gs://logging-natcap logging

# Grab the header of a file, then grab the contents from all other files.
concatenate-usage:
	$(FIND) logging -name "_usage*" -print -quit | xargs head -n1 > usage-all.csv
	$(FIND) logging -name "_usage*" | xargs grep /invest/ >> usage-all.csv
