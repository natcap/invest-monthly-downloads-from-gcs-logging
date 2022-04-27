# Aggregate our usage logging by month

## Setup

Because our raw usage logs take a long time to execute, run this on a system
that won't be interrupted. A google cloud VM is probably best, since we won't
be charged for bucket egress within the google network.

The system will also need these packages installed:

* `python3`
* `python3-pandas`
* The Google Cloud SDK (`gsutil`)
* GNU `make`, `grep`, `find`, `mkdir` and `xargs`

On a debian VM in google cloud, this command will suffice:

```bash
$ sudo apt update && sudo apt install python3 make python3-pip
$ sudo python3 -m pip install --prefer-binary --upgrade "pandas>=1.3.0"
```

## Command Execution

```bash
$ make all
```

This make command, `make all` will execute the following:

1. `gsutil rsync` to fetch the raw usage logs
2. We aggregate all of these CSV files together into large logfiles for easier
   parsing
3. We run a python script to summarize counts by month.

Note that steps 2 and 3 are automatically done for `invest` and
`invest-workspace`. As an output, you'll see `monthly-invest.csv` and
`monthly-invest-workbench.csv` in the CWD.
