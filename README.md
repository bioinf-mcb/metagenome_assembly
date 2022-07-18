# Metagenome_assembly
WDL Workflow for metagenome assembly:
![metagenomics-pipeline drawio](https://raw.githubusercontent.com/crusher083/metagenome_assembly/master/metagenomics-pipeline.drawio.png)
Python script to generate mapping between non-redundant gene catalogue and MAGS

## Introduction to WDL workflow
### This pipeline will perform;
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
 - `conda` for building the envronment 
    - `conda create -f pipeline.env`
 - Cromwell
    - `python src/setup_cromwell.py --save_path SAVE_PATH --config_path CONFIG_PATH`
 - Python 

## Running the pipeline
### 1. QC and assemble  
 - Requirements
   - `wgs_files` - path to directory with paired shotgun sequencing files
 - Output
   - quality controlled .fastq files
   - assembled contigs in `OUTPUT_DIR/assemble`
   - count table with read counts per sample
 ```sh
 # Process the data
 python src/qc_and_assemble.py -i wgs_files -o OUTPUT_DIR -t 8 -c 3 -bt2_index ./GRCh38_bt2
 ```

### 2. (...)

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
