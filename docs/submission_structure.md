I'm just going to rant out a bunch of information and we'll format it later.

## General program structure

Structure of zip

```
/metadata.yaml
/program.py    
```

Metadata should contain a command to run the submission, i.e.:

```yaml
# metadata.yaml
command: python program.py
```

## Student submission

Receives the following directories upon running:

...

#### Expected output:

Write any output to `/app/output`, this will be forwarded to the scoring program


## Ingestion program

Receives the following directories upon running:

...

#### Expected output:

Write any output to `/app/output`, this will be forwarded to the scoring program


## Scoring program

Receives the following directories upon running:

...

#### Expected output:

Write any output to `/app/output`, this will be forwarded to the scoring program

Scores should be written to `/app/output/scores.json`, where each score correlates to some
leaderboard key + column. For example, with the following leaderboard:

```yaml
leaderboards:
  - title: Pisano Period Leaderboard
    key: main
    columns:
      - title: CPU
        key: cpu
        index: 0
        sorting: desc
      - title: Mem
        key: mem
        index: 1
        sorting: desc
      - title: Char count
        key: char_count
        index: 2
        sorting: desc
```

You should write a scores json like so:
```json
{  
   "main":{  
      "cpu":0.25,
      "mem":0.1,
      "char_count":200
   }
}
```
