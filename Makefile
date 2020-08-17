.PHONY: download

download:
	-mkdir logging
	gsutil -m rsync -r gs://logging-natcap logging
