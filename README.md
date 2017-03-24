
# Viral Read Purification (VRP) Pipeline 



## Pipeline


1. Read QC
2. trim reads
3. find contaminating species
4. decontaminate by mapping / k-mers (?)
...



## Setup

### Pipeline

1. Install Python if you don't have it from before, and a cool python package - `Ruffus` (http://www.ruffus.org.uk/). 
Running jobs on a cluster (PBS, Slurm, etc) requires `drmaa` package. 
You might also need following packages: optparse, logging, shutil

2. Clone the pipeline repository:
`git clone https://github.com/seru71/vrp_pipeline.git <PIPELINE_HOME>`

3. Change directory to newly created pipeline dir, and checkout desired version (master by default)
```
cd <PIPELINE_HOME>
git checkout v0.1
```

The pipeline is ready now, but you will need all of its components to perform the analysis.

### Pipeline components

Install following tools:
1. FastQC
2. Trimmomatic (http://www.usadellab.org/cms/?page=trimmomatic)
3. MASH
4. BWA

And if your input is not yet converted to FASTQ, install also:  
6. bcl2fastq ()


### Reference data

Download reference genome of the bacteria you are planning to analyze.

## Usage

The NGS pipeline is run using `vpr_pipeline.py` script:

* Running the script

    You can run the script using `python <PIPELINE_HOME>/vpr_pipeline.py`.
    A list of possible options will be presented. The only required option is `--run_folder RUN_FOLDER`, 
    which specifies location of the run folder created by Illumina sequencer.
    
    Important part of the pipeline is the config file which contains paths to tools, reference genome, and docker settings.
    See an exemplary file for all required options in <PIPELINE_HOME>/vpr_pipeline.config
    If the settings file is not given as argument (--settings), it is expected in the RUN_FOLDER/vpr_pipeline.config
  
    If you want to follow progress of the script, use the verbose option (`-vvvvv`).
    In order to use multithreading, use the `-j` option (`-j 12`).

* Outputs

    The script will create RUN_ID folder in the scratch-root directory (given in settings). 
    Inside there will be several directories: 
    	SAMPLE_ID/ - one dir per sample, named after samples found in the RUN_FOLDER 
    	fastqs/    - fastq files
    	drmaa/     - SLURM scripts created automatically (if you are using SLURM; for debugging purposes)
    	qc/        - qc output

    After finishing, the sample directories will contain:
    	- assembled genome
   

* Typical usage

    For running the assembly using 12 concurrent threads:

	vpr_pipeline.py --run_folder /incoming/RUN_XXXX_YYYY_ZZZZZ \
						    --settings /my_project/ecoli.config \
							--target complete_run \
							-vvv -j 12 \
							--log_file /my_project/pipeline_run_XXX.log





