# Metagenome_assembly
WDL Workflow for metagenome assembly:
![metagenomics-pipeline drawio](https://raw.githubusercontent.com/crusher083/metagenome_assembly/master/metagenomics-pipeline.drawio.png)
Python script to generate a mapping between non-redundant gene catalogue and MAGS

## How this works? 
The wrapper scripts in Python (located in `src`) will prepare files and send them to `Cromwell`. Cromwell executes instructions written in Workflow definition Language (WDL; located in `src/wdl`). To avoid dependency conflicts `Cromwell` runs `Docker` containers with preinstalled software (dockerfiles located in `docker`). 

## Introduction to WDL workflow
### This pipeline will perform:
* Pre-processing of reads with Kneaddata
* Metagenomics assembly with Megahit
* Gene prediction
* Mapping of reads against the contigs 
* Metagenome binning using MetaBAT2 
* Quality assessment of genome bins
* Taxonomic classifications
* Gene clustering with CD-HIT-EST
* Mapping of reads to gene clusters and computing gene counts

## Requirements
 - `Docker`
 - `conda` for building the environment 
 - Python 

## 1. Installation
### 1. Clone the repository
 - `git clone www.github.com/crusher083/metagenome_assembly`
### 2. Create a conda environment
 - `conda env create -f pipeline.yml`
### 3. Install Cromwell  
Use the `setup_cromwell.py` script to download and install it.
    - `python src/setup_cromwell.py --save_path SAVE_PATH`
## 2. Run the pipeline!
### 1. Quality control and assembly 
This step will perform quality control of your reads with `Kneaddata` and assemble quality-controlled reads into contigs using `MegaHIT`.

 - Requirements
   - `input_folder` - path to directory with paired shotgun sequencing files (fastq.gz, fastq, fq.gz, fq formats)
   - `bt2_index` - path to a directory with a Bowite2 index. In case the folder doesn't contain an index, the user would be proposed to download GRCh38 index used for decontamination of metagenomic samples from human DNA.
    - `output_folder` - path to a directory where the results will be saved.
 - Optional arguments
   - `threads` - number of threads to use. (default: 1)
   - `concurrent_jobs` - number of concurrent jobs to run. (default: 1)
 - Output
   - quality controlled .fastq.gz files in `OUTPUT_FOLDER`
   - assembled contigs in `OUTPUT_FOLDER/assemble`
   - count table with read counts per sample `OUTPUT_FOLDER/kneaddata_count_table.tsv`
   - files needed for correct `Cromwell` run in `OUTPUT_FOLDER/system`
 ```sh
 # Process the data
 python src/qc_and_assemble.py -i input_folder -o OUTPUT_DIR -t 8 -c 3 -bt2_index ./GRCh38_bt2
 ```

### Then pipeline forks into two branches - taxonomical and functional 

### F - Functional annotation
#### F1 - Gene prediction
This step will perform gene recognition using `Prodigal`.
- Requirements
   - `input_folder` - path to directory with assembled contigs (located in `OUTPUT_FOLDER/assemble` of previous step)
   - `output_folder` - path to a directory where the results will be saved.
- Optional arguments
   - `concurrent_jobs` - number of concurrent jobs to run. (default: 1)
   - `suffix` - suffix, that helps to identify contigs and preserve consistent filenames (default: `.min500.contigs.fa`)
- Output
   - `SAMPLE_NAME.gff` - feature table in Genbank table
   - `SAMPLE_NAME.fna` - nucleotide sequences for genes in FASTA
   - `SAMPLE_NAME.faa` - protein translations for genes in FASTA

## Outputs
This pipeline will produce a number of directories and files
* assemble; contains assembled contigs
* predictgenes; gene coordinates file (GFF), protein translations and nucleotide sequences in fasta format
* metabat2; binned contigs and a summary report
* CheckM; genome assessment summary report
* gtdbtk; taxonomic classification summary file
* cluster_genes; representative sequences and list of clusters


## Mapping between gene catalogue, MAGS and eggNOG annotation
Python3 script to map non-redundant gene catalogue back to contigs, MAGS and eggNOG annotations 

## Input requirements
* clustering file - tab-delimited file with cluster ID and gene ID
* Non-redundant gene catalogue (fasta)
* Contig files in fasta
* binned contigs (MAGS) in fasta
* taxonomy files (tsv)
* EggNOG annotation file (tsv)

### Output
mapping table (tsv file) that links the non-redundant gene catalogue back to contigs, MAGs and to eggNOG annotations
