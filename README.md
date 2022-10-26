# Metagenomic assembly
WDL Workflow for metagenome assembly:
![metagenomics-pipeline drawio](https://raw.githubusercontent.com/crusher083/metagenome_assembly/master/metagenomics-pipeline.drawio.png)
Python script to generate a mapping between non-redundant gene catalog and MAGS

## How does this work? 
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
### Attention: The pipeline was tested on two samples with 4.3 Gb and 2.7 Gb in 2 parallel jobs, 16 CPU cores and 64 Gb RAM each. Time may vary significantly depending on your system and sequencing depth
### 1. Quality control and assembly 
This step will perform quality control of your reads with `Kneaddata` and assemble quality-controlled reads into contigs using `MegaHIT`.

 - Requirements
   - `input_folder` - path to directory with paired shotgun sequencing files. (`fastq.gz`, `fastq`, `fq.gz`, `fq`)
   - `bt2_index` - path to a directory with a Bowite2 index. In case the folder doesn't contain an index, the user would be proposed to download GRCh38 index used for the decontamination of metagenomic samples from human DNA.
    - `output_folder` - path to a directory where the results will be saved.
 - Optional arguments
   - `thread_num` - number of threads to use. (default: 1)
   - `concurrent_jobs` - number of concurrent jobs to run. (default: 1)
 - Output
   - quality controlled .fastq.gz files in `OUTPUT_FOLDER`
   - assembled contigs in `OUTPUT_FOLDER/assemble`.
   - count table with read counts per sample `OUTPUT_FOLDER/kneaddata_count_table.tsv`.

```sh
# Qualirty control raw reads and assemble contigs 
python src/qc_and_assemble.py -i INPUT_FOLDER -o OUTPUT_FOLDER \
-bt2_index FOLDER_WITH_BT2_INDEX \
-t 8 -c 3 
```
```sh
INFO:root:Treating /storage/TomaszLab/vbez/metagenomic_gmhi/metagenomome_assembly/databases/GRCh38_bt2 as directory with bowtie2 index.
INFO:root:I inferred that _1 and _2 distinguish paired end reads.
INFO:root:Found samples: 2
DEBUG:root:Creating output directory: qc_assemble_out
DEBUG:root:Creating output directory: qc_assemble_out/system
[17:09:48] Workflow started succesfully. Please, be patient.  
[17:16:09] Workflow finished successfully.   
```

## Then pipeline forks into two branches - taxonomical and functional 

### T - Taxonomical annotation 

#### T1 - MAG assembly and taxonomic classification
This step will bin contigs using `MetaBAT2`, check bins for quality and contamination using `CheckM` and assign taxonomical classification for MAGs using `GTDB`.
- Requirements
   - `input_folder_reads` - a path to a directory with QCed reads (located in `OUTPUT_FOLDER/` of `qc and assembly` step).
   - `input_folder_contigs` - a path to a directory with assembled contigs (located in `OUTPUT_FOLDER/assemble` of `qc and assembly` step).
   - `gtdbtk_data` - a path to a directory with a GTDB-Tk database release. In case the folder doesn't contain the data, it will be downloaded automatically.
   - `output_folder` - a path to a directory where the results will be saved.
- Optional arguments
   - `thread_num` - number of threads to use. (default: 1)
   - `concurrent_jobs` - number of concurrent jobs to run. (default: 1)
   - `suffix` - suffix, that helps to identify contigs and preserve consistent filenames. (default: `.min500.contigs.fa`)
   - `suffix1` - suffix, that helps to identify forward reads. (default: `_paired_1.fastq.gz`)
   - `suffix2` - suffix, that helps to identify reverse reads. (default: `_paired_2.fastq.gz`)
- Output
   - `SAMPLE_NAME.gff` - feature table in Genbank table.
   - `SAMPLE_NAME.fna` - nucleotide sequences for genes in FASTA.
   - `SAMPLE_NAME.faa` - protein translations for genes in FASTA.
```sh
# Bin, check and taxonomically classify MAGs
python src/t1_predict_mags.py -ir INPUT_FOLDER_READS -s1 _paired_1.fastq.gz -s2 -s1 _paired_2.fastq.gz \ 
-ic INPUT_FOLDER_CONTIGS -s .min500.contigs.fa \
-gtdb ../databases/gtdbtk-data/ -o OUTPUT_FOLDER \
-t 24 -c 2 
```
```
DEBUG:root:Creating output directory: out_mags
DEBUG:root:Creating output directory: out_mags/system
[17:23:29] Workflow started succesfully. Please, be patient.  
[17:40:13] Workflow finished successfully.
```
### F - Functional annotation
#### F1 - Gene prediction
This step will perform gene recognition using `Prodigal`.
- Requirements
   - `input_folder` - a path to a directory with assembled contigs (located in `OUTPUT_FOLDER/assemble` of the `qc and assembly` step).
   - `output_folder` - a path to a directory where the results will be saved.
- Optional arguments
   - `concurrent_jobs` - number of concurrent jobs to run. (default: 1)
   - `suffix` - suffix, that helps to identify contigs and preserve consistent filenames. (default: `.min500.contigs.fa`)
- Output
   - `SAMPLE_NAME.gff` - feature table in Genbank table.
   - `SAMPLE_NAME.fna` - nucleotide sequences for genes in FASTA.
   - `SAMPLE_NAME.faa` - protein translations for genes in FASTA.
```sh
# Predict genes
python src/f1_predict_genes.py -i INPUT_FOLDER -s .min500.contigs.fa -o OUTPUT_FOLDER   \
-c 3
```

```sh
DEBUG:root:Creating output directory: OUTPUT_FOLDER
DEBUG:root:Creating output directory: OUTPUT FOLDER/system
[15:19:43] Workflow started succesfully. Please, be patient.
[15:21:29] Workflow finished successfully.       
```
#### F2 - Gene clustering 
This step will cluster genes using `CD-HIT` and sequence similarity threshold.
- Requirements
   - `input_folder` - a path to a directory with predicted nucleotide sequences of genes (`OUTPUT_FOLDER/*.fna` of the previous step).
   - `output_folder` - a path to a directory where the results will be saved.
- Optional arguments
   - `thread_num` - number of threads. (default: 1)
   - `suffix` - suffix, that helps to identify contigs and preserve consistent filenames. (default: `.fna`)
- Output
   - `gene_catalogue_split` - gene cataloge split in chunks of 10,000 sequences for further analysis.
   - `combined_genepredictions.sorted.fna` - combined predictions of complete genes sorted by length.
   - `nr.fa` - full gene catalogue.
   - `nr.fa.clstr` - clustered genes.
   - `kma_db.tar.gz` - KMA database - required for quantification of gene copies in bacterial genomes (next step).  
```sh
# Cluster genes
python src/f2_generate_gene_catalog.py -i INPUT_FOLDER -s .fna -o OUTPUT_FOLDER \
-t 16
```

```sh
DEBUG:root:Creating output directory: OUTPUT_FOLDER
DEBUG:root:Creating output directory: OUTPUT FOLDER/system
[15:23:26] Workflow started succesfully. Please, be patient.
[15:24:56] Workflow finished successfully.     
```

#### F3 - Map to gene clusters 
This step will quantify the number of gene clusters in sequenced reads aligning it to the reference using `KMA`.
- Requirements
   - `input_folder` - a path to a directory with quality-controlled reads (from the `qc_and_assembly` step).
   - `database` - a path to a KMA database. (from `F2 - Gene clustering` step) 
   - `output_folder` - a path to a directory where the results will be saved.
- Optional arguments
   - `suffix1` - suffix, that helps to identify forward reads. (default: `_paired_1.fastq.gz`)
   - `suffix2` - suffix, that helps to identify reverse reads. (default: `_paired_2.fastq.gz`)
   - `thread_num` - number of threads. (default: 1)
- Output
   - `SAMPLE_NAME.kma.res` - KMA full output.
   - `SAMPLE_NAME.geneCPM.txt` - table with extracted and normalized gene counts (count per million).
```sh
# Quantify gene clusters
python src/f3_generate_gene_catalog.py -i INPUT_FOLDER -s1 _paired_1.fastq.gz -s2 _paired_2.fastq.gz \
-db F2_OUTPUT_FOLDER/kma_db.tar.gz \
-o OUTPUT_FOLDER \
-t 16
```

```sh
DEBUG:root:Creating output directory: OUTPUT_FOLDER
DEBUG:root:Creating output directory: OUTPUT FOLDER/system
[15:26:48] Workflow started succesfully. Please, be patient.
[15:29:08] Workflow finished successfully.     
```

#### F4 - Annotate gene catalog
This step will provide functional annotation of gene clusters from both `eggNOG-mapper` and `DeepFRI`.
- Requirements
   - `input_folder` - a path to a directory with gene catalog split into chunks of 10,000 reads (from `F2 - gene clustering` step).
   - `eggnog_database` - a path to an `eggNOG-mapper` database. If it is not located in the folder, the necessary files will be downloaded automatically.
   - `output_folder` - a path to a directory where the results will be saved.
- Optional arguments
   - `suffix` - suffix, that helps to gene catalog chunks. (default: `.fa`)
   - `thread_num_` - number of threads. (default: 1)
   - `concurrent_jobs` - number of jobs to run in parallel. A single `DeepFRI` job requires 55GB of RAM, too many jobs may result in an out-of-memory error.
- Output
   - `deepfri_annotations.csv` - `DeepFRI` functional annotation for a gene catalog.
   - `nr-eggnog.emapper.annotations` - `eggNOG-mapper` functional annotation for a gene catalog.
   - `nr-eggnog.emapper.seed_orthologs`- a file with the results from parsing the hits. Each row links a query with a seed ortholog. 
```sh
# Annotate gene catalog
python src/f4_annotate_gene_catalog.py 
-i F2_OUTPUT_FOLDER/gene_catalog_split/ -s .fa \
-db eggNOG-DATABASE \
-o OUTPUT_FOLDER \
-t 16 -c 2
```

```sh
INFO:root:Treating /storage/TomaszLab/vbez/metagenomic_gmhi/metagenomome_assembly/databases/eggnog-data as directory with eggNOG.
INFO:root:Treating /storage/TomaszLab/vbez/metagenomic_gmhi/metagenomome_assembly/databases/eggnog-data as directory with Diamond.
DEBUG:root:Creating output directory: OUTPUT_FOLDER
DEBUG:root:Creating output directory: OUTPUT_FOLDER/system
[15:56:27] Workflow started succesfully. Please, be patient.                                            
[16:47:31] Workflow finished successfully.  

```

### Generate final output
This step will collect all the output into one table. 
- Requirements
   - `contig_folder` - a path to a directory with contigs from the `qc_and_assembly` step.
   - `bins_folder` - a path to a directory with bins from the `T1 - MAGs binning` step.
   - `gtdbtk_folder` - a path to a directory with GTDB-Tk results from the `T1 - MAGs binning` step.
   - `checkm_folder` - a path to a directory with CheckM results from the `T1 - MAGs binning` step.
   - `gene_catalog` - a path to a gene catalog file from the `F2 - gene clustering` step.
   - `gene_cluster_file` - a path to a file with gene clusters.
   - `eggnog_annotations` - a path to a file with `eggNOG-mapper` annotations.
   - `deepfri_annotations` - a path to a file with `DeepFRI` annotations.
   - `output_folder` - a path to a directory where the results will be saved.
## Outputs
   - `_individual_mapped_genes.tsv` - genes clusters mapped to MAGs.
   - `_MAGS.tsv` - MAGs summary from `GTDB-tk` and `CheckM`.
   - `_mapped_genes_cluster.tsv` - `eggNOG-mapper` annotations for gene clusters.
   - `merged_eggnog_output.tsv` - `eggNOG-mapper` annotations for gene clusters.
   - `merged_deepfri_output.tsv` - `DeepFRI` annotations for gene clusters.