# Metagenome_assembly
WDL Workflow for metagenome assembly
Python script that generate mapping between non-redundant gene catalogue and MAGS

# Introduction to WDL workflow
### This pipeline will perform;
* Pre-processing of reads with Trim Galore and Kneaddata
* Metagenomics assembly with Megahit
* Gene prediction
* Mapping of reads against the contigs 
* Metagenome binning using MetaBAT2 
* Quality assessment of genome bins
* Taxonomic classifications
* Gene clustering with CD-HIT-EST
* Mapping of reads to gene clusters and computing gene counts

# Usage 
## Requirements

This pipeline uses docker image 

# Input parameters 
All the inputs needed by the workflow are provided through a JSON file and can be generated using [Womtool](https://cromwell.readthedocs.io/en/stable/WOMtool/) with the following command  

java -jar womtool.jar inputs workflow.wdl > inputs.json

# Running the pipeline
### Locally:
The pipeline can be run using [Cromwell](https://cromwell.readthedocs.io/en/stable/)

java -jar cromwell.jar run workflow.wdl -i inputs.json 


# Outputs
This pipeline will produce a number of directories and files
* assemble; contains assembled contigs
* predictgenes; gene coordinates file (GFF), protein translations and nucleotide sequences in fasta format
* metabat2; binned contigs and a summary report
* CheckM; genome assessment summary report
* gtdbtk; taxonomic classification summary file
* cluster_genes; representative sequences and list of clusters


# Mapping between genes to MAGS and eggNOG annotation
Python3 script to map non-redundant gene catalogues to contigs, MAGS and eggNOG annotations 

# Runtime dependencies
The following softwares are required by python script:
* [Click] (https://palletsprojects.com/p/click/)
* [NumPy] (https://numpy.org/)
* [Pandas] (https://pandas.pydata.org/)
* [scikit-bio] (http://scikit-bio.org/)

# Usage
python genes_MAGS_eggNOG_mapping.py --help

## Input Requirements
* clustering file: tab-delimited file with cluster ID and gene ID
* Non-redundant gene catalogue (fasta)
* Contig files in fasta
* binned contigs (MAGS) in fasta
* taxonomy files (tsv)
* EggNOG annotation file (tsv)

# Output
mapping table (tsv file) that links the non-redundant gene catalogue back to contigs, MAGs and to  eggNOG annotations







