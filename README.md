# DroneCrashDetection

Repository for Drones Crash Detection  and Analysis

## Folder Structure 

```
├── main_run.ipynb  - here's an example of main_runm that is responsible for
      running the dataloader and failure detection procedure     
│
│
├── analysis          - this folder contains jupyter notebooks and pickle files 
for correlation and causation analysis
│    └── causality_analysis.ipynb
│    └── correlation_analysis.ipynb
│    └── grangercausality_test.py -- Module for Granger Causality Test
│    └── dt -- This folder contains pickle files used in causality analysis
├── db               - this folder contains the database module
│    └── database.py
├── failure_detector               - this folder contains the failure detector module
│    └── failuredetector.py
│
├── dtloader             - this folder contains the dataloader module
│    └── dataloader.py
│
|
├── testing         - this folder contains the unittesting module for failure detection methods
│    └── failuretest.py
│
│
├── report             - this folder contains the report files for the project
│   └── phase 2
│
│
├── stats_files       - this folder contains files resulted from analysis 
|
├── data       - this folder contains log files 
│
│
└── utils               - this folder contains any utils you need.
    ├── utils.py      - util functions for use in multiple modules and analysis.
```

## Other
