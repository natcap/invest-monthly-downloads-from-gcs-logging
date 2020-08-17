.PHONY: download

download:
	-mkdir logging
	gsutil -m rsync gs://logging-natcap logging
