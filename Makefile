.PHONY: download all

# Must be GNU find.
# May need to set this on Windows.
FIND := find
PYTHON := python3

# -j enables gzip compression
# -x excludes files matching the provided regular expression.
download:
	-mkdir logging
	gsutil -m rsync -r -j "" -x ".*_storage.*" gs://logging-natcap logging

# Grab the header of a file, then grab the contents from all other files.
#
# See https://www.gnu.org/software/make/manual/html_node/Automatic-Variables.html
# $@ is the file name of the target of the rule
# $< is the name of the first prerequisite.
usage-%.csv:
	$(FIND) logging -name "_usage*" -print -quit | xargs head -n1 > $@
	$(FIND) logging -name "_usage*" | xargs grep --no-filename /$(subst usage-,,$@)/ >> $@

monthly-%.csv: usage-%.csv
	$(PYTHON) monthly-count.py $<

all: download monthly-invest.csv monthly-invest-workbench.csv
