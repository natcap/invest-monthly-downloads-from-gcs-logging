# Scripts for extracting logging from bucket state


## Synchronize state

```
$ make download
```

## Concatenate some months of logging to a single file

```
# NOTE: use bash expansion for this
$ ls logging/releases.naturalcapitalproject.org/_usage_2020_{03..08}_* | xargs cat > concatenated.txt
```
