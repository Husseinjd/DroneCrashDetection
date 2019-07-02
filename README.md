# DroneCrashDetection

Repository for Automatic Diagnosis of Drone Crashes

## Folder Structure 

```
├── main_run.ipynb  - here's an example of main_run that is responsible for
      running the dataloader and failure detection procedure     
│
│
├── analysis          - this folder contains jupyter notebooks for analysis and visualisations
│                        for correlation and causation analysis
│    └── segmentation_analysis.ipynb 
│    └── correlation_analysis.ipynb
│
├── granger                         - this folder contains required modules and notebooks for the granger causality tests
│    └── causality_utils.py         - utilities to use granger causality in analysis (data cleaning , preprocessing etc..)
│    └── grangercausality_cl.py     - classification granger causality
│    └── grangercausality_reg.py    - regression granger causality
│    └── causality_analysis.py      - applying granger causality to dataset + viz 
│    
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
├── report             - this folder contains the report files for the project / full report in exercises
│     └── phase 2
│     └── phase 3
│  
├── segmentation             - this folder contains the segmentation required modules
│   └── segmentation.py
│   └── segment.py
│
├── stats_files       - this folder contains files resulted from analysis 
|
├── data               - this folder contains log files 
│
│
└── utils               - this folder contains any utils you need.
    ├── utils.py        - util functions for use in multiple modules and analysis.
    ├── feature_eng.py  - feature engineering fuctions used for granger causality classification
```

## Other
