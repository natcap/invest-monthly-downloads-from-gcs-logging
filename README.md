# Scripts for extracting logging from bucket state


## Synchronize state

```
$ make download
```

## Concatenate some months of logging to a single file

```
# NOTE: use bash expansion for this
$ ls logging/releases.naturalcapitalproject.org/_usage_2020_0{3..8}_* | xargs cat > concatenated.txt
```

## Get mac download count

```
$ grep InVEST.*mac concatenated.txt | sort | uniq | wc -l
```

## Get windows download count

```
$ grep Setup concatenated.txt | sort | uniq | wc -l
