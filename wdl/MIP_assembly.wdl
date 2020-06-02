# WDL workfow for metagenome assembly

# Description
# This WDL workflow perfoms the following tasks;
# quality control of the metagenomics sequences using Trim Galore and KneadData 
# runs assembly using Megahit
# gene prediction using prodigal
# Aligns reads against the contigs using BWA
# metagenomics binning using MetaBAT
# assessment of the quality of the genome using CheckM
# taxonomic classifications using gtdbtk
# cluster genes with CD-Hit 
# mapping of reads against the non-redundant gene catalog and computing read counts for every gene

# workflow
workflow MIP_assembly {
    # specfying paths to the data
    File Sample_Path_List
    String Fastq1_Extension
    String Fastq2_Extension
    Array[Array[String]] SamplesPaths = read_tsv(Sample_Path_List)
    scatter (pair in SamplesPaths){

        String SampleDir = pair[1]
        String sample = pair[0]
        File F1 = SampleDir + sample + Fastq1_Extension
        File F2 = SampleDir + sample + Fastq2_Extension
	# specifying tasks to be executed
        call qcAdapters {
            input: 
            sample=sample, 
            file1=F1, 
            file2=F2
        }
        call kneadData {
            input: 
            sample=sample, 
            file1=qcAdapters.fileR1, 
            file2=qcAdapters.fileR2
        }
        call assemble {
            input: 
            sample=sample, 
            r1=kneadData.fileR1, 
            r2=kneadData.fileR2, 
            s1=kneadData.fileS1, 
            s2=kneadData.fileS2
        }

        call predictgenes {
            input: 
            sample=sample, 
            fileContigs=assemble.fileContigs
        }

        call map_to_contigs { 
            input: 
            fileR1=kneadData.fileR1,
            fileR2=kneadData.fileR2,
            sample=sample,
            contigs=assemble.fileContigs
        }

        call metabat2 {
            input:
            contigs=assemble.fileContigs,
            sample=sample,
            bam=map_to_contigs.fileBAM
        }

        call checkm {
            input:
            bins=metabat2.bins,
            sample=sample
        }

        call gtdbtk {
            input:
            bins=metabat2.bins,
            sample=sample
        }
    }


    call kneaddataReadCountTable {
        input:
        logFiles=kneadData.log_file
    }

    call cluster_genes { 
        input: 
        genepredictions=predictgenes.fileFNA 
    }

    call annotate_gene_catalogue {
        input:
        gene_catalogue=cluster_genes.nrFa 
    }

    scatter (gene_shard in cluster_genes.nr_split){

        call annotate_deepfri {
            input:
            gene_catalogue=gene_shard 
        }
    }

    call genes_to_mags_mapping {
        input:
        contigs=assemble.fileContigs,
        deepfri_output=annotate_deepfri.deepfri_out,
        gene_catalogue=cluster_genes.nrFa,
        gene_clusters=cluster_genes.nrClusters,
        eggnog_annotations=annotate_gene_catalogue.eggnog_annotations,
        metabat2_bins=metabat2.bins,
        gtdbtk_output=gtdbtk.gtdbtk_summary
    }

    Array[Pair[File, File]] fileR1R2 = zip(kneadData.fileR1, kneadData.fileR2) 
    
    scatter (pair in fileR1R2){

            String currentSample = basename(pair.left, ".adapterTrimmed.1_kneaddata_paired_1.fastq.gz")

            call map_to_gene_clusters { 
            input: 
            fileR1=pair.left,
            fileR2=pair.right,
            sample=currentSample,
            nrFa=cluster_genes.nrFa,
            nrFai=cluster_genes.nrFai,
            ref1=cluster_genes.nrRef1,
            ref2=cluster_genes.nrRef2,
            ref3=cluster_genes.nrRef3,
            ref4=cluster_genes.nrRef4,
            ref5=cluster_genes.nrRef5
        }
    }

}

# this task will trim the adapter sequences using trim galore
task qcAdapters {
    File file1
    File file2
    String sample

    command {

        # move file into name that fits with the sample naming strategy
        mv ${file1} ${sample}.1.fq.gz
        mv ${file2} ${sample}.2.fq.gz

        trim_galore --paired --phred33 --quality 0 --stringency 5 --length 10 \
        ${sample}.1.fq.gz ${sample}.2.fq.gz

        mv ${sample}.1_val_1.fq.gz ${sample}.adapterTrimmed.1.fq.gz
        mv ${sample}.2_val_2.fq.gz ${sample}.adapterTrimmed.2.fq.gz
    }
    
    output {
        File fileR1 = "${sample}.adapterTrimmed.1.fq.gz"
        File fileR2 = "${sample}.adapterTrimmed.2.fq.gz"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:070318"
        cpu: 1
        memory: "1GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 40 SSD"
    }
}

# quality control of metagenomics sequences
# removing host DNA contamination

task kneadData {
    File file1
    File file2
    String sample
    File ref_homo_sapiens

    command {
        mkdir ref_homo_sapiens
        tar -xf ${ref_homo_sapiens} -C ref_homo_sapiens/

        kneaddata --input ${file1} --input ${file2} -o . \
          -db ref_homo_sapiens \
          --trimmomatic-options "HEADCROP:15 SLIDINGWINDOW:4:15 MINLEN:50" \
          -t 4 \
          --log ${sample}.log \
          --reorder
        
        gzip ${sample}.adapterTrimmed.1_kneaddata_paired_1.fastq
        gzip ${sample}.adapterTrimmed.1_kneaddata_paired_2.fastq
        gzip ${sample}.adapterTrimmed.1_kneaddata_unmatched_1.fastq
        gzip ${sample}.adapterTrimmed.1_kneaddata_unmatched_2.fastq

    }
    
    output {
        File fileR1 = "${sample}.adapterTrimmed.1_kneaddata_paired_1.fastq.gz"
        File fileR2 = "${sample}.adapterTrimmed.1_kneaddata_paired_2.fastq.gz"
        File fileS1 = "${sample}.adapterTrimmed.1_kneaddata_unmatched_1.fastq.gz"
        File fileS2 = "${sample}.adapterTrimmed.1_kneaddata_unmatched_2.fastq.gz"
        File log_file = "${sample}.log"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:101419"
        cpu: 4
        memory: "24GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 501 SSD"
    }
}

task kneaddataReadCountTable {
    Array[String] logFiles

    command {
        
        cat ${write_lines(logFiles)} > logFiles_2_download.txt
        mkdir dir_logfiles
        cat logFiles_2_download.txt | gsutil -m cp -I dir_logfiles/
        
        kneaddata_read_count_table --input dir_logfiles/ --output kneaddata_read_count_table.tsv

    }

    output {
        File kneaddataReadCountTable = "kneaddata_read_count_table.tsv"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:101419"
        cpu: 1
        memory: "4GB"
        preemptible: 2
        disks: "local-disk 50 HDD"
        maxRetries: 2
    }
}

# metagenomics assembly using megahit

task assemble {
    File r1
    File r2
    File s1
    File s2
    String sample

    command <<<
        rm -f assemble
        megahit -1 ${r1} -2 ${r2} -r ${s1},${s2} -t 4 -m 15000000000 -o assemble
        cat assemble/final.contigs.fa | \
        awk -v var="${sample}" '
            {if($0 ~ /^>/) {contigName=substr($0, 2,length($0))} 
            else {seq=$0; if(length($0) >= 500) {print ">"var"_"contigName"\n"seq}} }' > assemble/${sample}.min500.contigs.fa
    >>>

    output {
        File fileContigs = "assemble/${sample}.min500.contigs.fa"
    
}   runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:081518"
        cpu: 4
        memory: "15GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 100 SSD"
    }
}
# gene prediction with prodigal
task predictgenes {
    File fileContigs
    String sample

    command <<<
        mkdir prodigal
        if [[ `wc -l ${fileContigs} | awk '{print $1}'` == "0" ]]; then
            touch prodigal/${sample}.gff
            touch prodigal/${sample}.fna
            touch prodigal/${sample}.faa
        else
            prodigal -p meta -i ${fileContigs} -f gff \
            -o prodigal/${sample}.gff \
            -d prodigal/${sample}.fna \
            -a prodigal/${sample}.faa \
            2> prodigal/prodigal.stderr > prodigal/prodigal.out
        fi
    >>>
    
    output {
        File fileFNA = "prodigal/${sample}.fna"
        File fileFAA = "prodigal/${sample}.faa"
        File fileGFF = "prodigal/${sample}.gff"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:081518"
        cpu: 1
        memory: "7GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 100 SSD"
    }
}
# mapping of reads against the assembled contigs with Burrow-wheeler aligner
task map_to_contigs {
    File fileR1
    File fileR2
    String sample
    File contigs

    command {
        # indexing contigs file with BWA and Samtools
        bwa index ${contigs}
        samtools faidx ${contigs}

        bwa mem -t 8 -M ${contigs} ${fileR1} ${fileR2} | \
        samtools view - -h -Su -F 2308 -q 0 | \
	# sorting BAM file with Samtools
        samtools sort -@ 8 -m 2G -O bam -o ${sample}.sort.bam 

    }
    
    output {

        File fileBAM = "${sample}.sort.bam"

    }
    
    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:082018"
        cpu: 8
        memory: "24GB"
        preemptible: 2
        maxRetries: 3
        bootDiskSizeGb: 50
        disks: "local-disk 200 SSD"
    }
}
# clustering metagenomic contigs into bins
task metabat2 {
    File bam
    String sample
    File contigs

    command {
        
        runMetaBat.sh ${contigs} ${bam}
        mv ${sample}.min500.contigs.fa.depth.txt ${sample}.depths.txt
        mv ${sample}.min500.contigs.fa*/ ${sample}_bins
        tar -cf ${sample}.bins.tar ${sample}_bins
        gzip ${sample}.bins.tar

    }
    
    output {

        File bins = "${sample}.bins.tar.gz"
        File depths = "${sample}.depths.txt"

    }
    
    runtime {
        docker: "gcr.io/microbiome-xavier/metabat2:021420"
        cpu: 8
        memory: "12GB"
        preemptible: 2
        maxRetries: 3
        bootDiskSizeGb: 50
        disks: "local-disk 100 SSD"
    }
}
# assessing completeness of the genome
task checkm {
    File bins
    String sample

    command {

        checkm data setRoot /checkm-data
        tar -xvf ${bins}
        checkm lineage_wf -f ${sample}_checkm.txt -t 4 -x fa ${sample}_bins/ ${sample}_checkm
        #checkm lineage_wf -t 10 -x fa ${sample}_bins/ ${sample}_checkm
        tar -cf ${sample}_checkm.tar ${sample}_checkm
        gzip ${sample}_checkm.tar

    }

    output {

        File checkm_summary = "${sample}_checkm.txt"
        File checkm_out = "${sample}_checkm.tar.gz"

    }

    runtime {
        docker: "gcr.io/microbiome-xavier/checkm:v1.1.2"
        cpu: 4
        memory: "100GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 100 HDD"
    }
}
# taxonomic classifications  
task gtdbtk {
    File bins
    File gtdb_reference
    String gtdb_release
    String sample

    command {

        tar -xf ${gtdb_reference} -C /gtdbtk-data/
        export GTDBTK_DATA_PATH=/gtdbtk-data/${gtdb_release}/
        tar -xf ${bins}
        gtdbtk classify_wf --genome_dir ${sample}_bins/ -x fa --cpus 4 --out_dir ${sample}_gtdb
        tar -czf ${sample}_gtdb.tar.gz ${sample}_gtdb
        cp ${sample}_gtdb/classify/gtdbtk.bac120.summary.tsv ${sample}.bac120.summary.tsv

    }

    output {

        File gtdbtk_out = "${sample}_gtdb.tar.gz"
        File gtdbtk_summary = "${sample}.bac120.summary.tsv"

    }

    runtime {
        docker: "gcr.io/microbiome-xavier/gtdbtk:v1.0.2"
        cpu: 4
        memory: "128GB"
        preemptible: 2
        maxRetries: 3
        bootDiskSizeGb: 50
        disks: "local-disk 100 SSD"
    }
}
# gene clustering with CD-HIT 
task cluster_genes {
    Array[File] genepredictions

    command <<<
        cat ${sep=' ' genepredictions} > combined_genepredictions.fna
        /app/extract_complete_gene.py combined_genepredictions.fna > combined_genepredictions.complete.fna

        usearch8.1.1861_i86linux64 \
          -derep_fulllength combined_genepredictions.complete.fna \
          -fastaout combined_genepredictions.derep.fna \
          -minseqlength 1

        usearch8.1.1861_i86linux64 \
          -sortbylength combined_genepredictions.derep.fna \
          -fastaout combined_genepredictions.sorted.fna \
          -minseqlength 1

        cd-hit-est -i combined_genepredictions.sorted.fna -T 32 -aS 0.9 -c 0.95 -M 0 -r 0 -B 0 -d 0 -o nr.fa

        bwa index nr.fa
        samtools faidx nr.fa

        # split nr.fa into files with 10,000 sequences each
        awk 'BEGIN {n_seq=0;n_file=1} /^>/ {if(n_seq%10000==0){file=sprintf("nr_%d.fa",n_file);n_file++} print >> file; n_seq++; next;} { print >> file; }' < nr.fa
    >>>

    output { 
        File combined_genepredictions = "combined_genepredictions.sorted.fna" 
        File nrFa = "nr.fa"
        File nrClusters = "nr.fa.clstr"
        File nrFai = "nr.fa.fai"
        File nrRef1 = "nr.fa.bwt"
        File nrRef2 = "nr.fa.pac"
        File nrRef3 = "nr.fa.ann"
        File nrRef4 = "nr.fa.amb"
        File nrRef5 = "nr.fa.sa"
        Array[File] nr_split = glob("nr_*.fa")
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:032819"
        cpu: 32
        memory: "120GB"
        bootDiskSizeGb: 50
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 500 SSD"
    }
}

task annotate_gene_catalogue {
    File gene_catalogue
    File eggnog_db
    File eggnog_db_diamond

    command {
        gunzip -c ${eggnog_db} > /app/eggnog-mapper-2.0.1/data/eggnog.db
        gunzip -c ${eggnog_db_diamond} > /app/eggnog-mapper-2.0.1/data/eggnog_proteins.dmnd

        python /app/eggnog-mapper-2.0.1/emapper.py --cpu 10 -i ${gene_catalogue} --output nr-eggnog --output_dir . -m diamond -d none --tax_scope auto --go_evidence non-electronic --target_orthologs all --seed_ortholog_evalue 0.001 --seed_ortholog_score 60 --query-cover 20 --subject-cover 0 --translate --override

    }

    output {
        File eggnog_annotations = "nr-eggnog.emapper.annotations"
        File eggnog_seed_orthologs = "nr-eggnog.emapper.seed_orthologs"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/eggnog-mapper:v2.0.1"
        cpu: 10
        memory: "16GB"
        bootDiskSizeGb: 100
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 200 HDD"
    }

}

task annotate_deepfri {
    File gene_catalogue

    command {
        /bin/python3 /app/scripts/cromwell_process_fasta.py -i ${gene_catalogue} -o deepfri_annotations.csv -m /app
    }

    output {
        File deepfri_out = "deepfri_annotations.csv"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/deepfried-api:051920"
        cpu: 2
        memory: "8GB"
        bootDiskSizeGb: 100
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 200 HDD"
    }
}


# mapping reads against non-redundant gene catalog
task map_to_gene_clusters {
    File fileR1
    File fileR2
    String sample
    File nrFa
    File nrFai
    File ref1
    File ref2
    File ref3
    File ref4
    File ref5

    command {
        
        bwa mem -t 8 -M ${nrFa} ${fileR1} ${fileR2} | \
        samtools view - -h -Su -F 2308 -q 0 | \
        samtools sort -n -@ 8 -m 2G -O bam -o ${sample}.sort.bam 

        /app/bamfilter_mate_saver.py -i ${sample}.sort.bam -o ${sample}.sort.filtered.ID95.bam -f 0.95

        # generating mapping statistics
	samtools flagstat ${sample}.sort.filtered.ID95.bam > ${sample}.ID95.flagstat.txt
	# computing the number of reads that fall into specific genomic region 
        /app/bam2counts.py -t 1 -y 1  -s ${sample} -v ${nrFai} -c ${sample}.count.txt -a ${sample}.abundance.txt -l ${sample}.learn.txt -i ${sample}.sort.filtered.ID95.bam

        cut -f1 ${sample}.count.txt > gene.names.txt
        cut -f2 ${sample}.count.txt > tmp.count.txt
        cut -f2 ${sample}.abundance.txt > tmp.abundance.txt
        
        mv tmp.count.txt ${sample}.count.txt
        mv tmp.abundance.txt ${sample}.abundance.txt

    }
    
    output {
        File fileBAM = "${sample}.sort.bam"
        File fileBAMfiltered = "${sample}.sort.filtered.ID95.bam"
        File fileFlagStat = "${sample}.ID95.flagstat.txt"
        File fileLearn = "${sample}.learn.txt"
        File fileCount = "${sample}.count.txt"
        File fileAbundance = "${sample}.abundance.txt"
        File fileGenes = "gene.names.txt"


    }
    
    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:082018"
        cpu: 8
        memory: "24GB"
        preemptible: 2
        maxRetries: 3
        bootDiskSizeGb: 50
        disks: "local-disk 200 SSD"
    }
}

task genes_to_mags_mapping {
    Array[File] contigs
    Array[File] deepfri_output
    File gene_catalogue
    File gene_clusters
    File eggnog_annotations
    Array[File] metabat2_bins
    Array[File] gtdbtk_output

    command {

        # concatenate contigs together to merged_min500.contigs.fa
        cat ${write_lines(contigs)} > contig_fasta.txt
        while read fasta_file; do
            cat $fasta_file >> merged_min500.contigs.fa
        done <contig_fasta.txt

        # concatenate DeepFrier outpus into one file
        cat ${write_lines(deepfri_output)} > deepfri_output.txt
        while read deepfri_file; do
            cat $deepfri_file >> merged_deepfri_output.csv
        done <deepfri_output.txt

        # extract MAGs to directory 'bins'
        mkdir bins
        cat ${write_lines(metabat2_bins)} > metabat2_bins.txt
        while read bin_file; do
            tar -xf $bin_file -C bins/
        done <metabat2_bins.txt

        # copy GTDBTk output summaries to directory gtdbtk
        mkdir gtdbtk
        cat ${write_lines(gtdbtk_output)} > gtdbtk_2_download.txt
        while read gtdbtk_file; do
            cp $gtdbtk_file gtdbtk/
        done <gtdbtk_2_download.txt

        python3 /app/genes_MAGS_eggNOG_mapping.py \
            --genes_file ${gene_catalogue} \
            --cluster_file ${gene_clusters} \
            --contigs_file merged_min500.contigs.fa \
            --eggnog_ann_file ${eggnog_annotations} \
            --bin_fp bins \
            --tax_fp gtdbtk \
            --out_gene_mapping_file gene_mapping.tsv \
            --out_cluster_taxa_file gene_clusters_taxa.tsv

    }
    
    output {
        File gene_mag_mappings = "gene_mapping.tsv"
        File gene_cluster_taxa_mappings = "gene_clusters_taxa.tsv"
        File merged_deepfri_out = "merged_deepfri_output.csv"
    }
    
    runtime {
        docker: "gcr.io/microbiome-xavier/gene-mapper:052820"
        cpu: 2
        memory: "8GB"
        preemptible: 2
        maxRetries: 3
        bootDiskSizeGb: 50
        disks: "local-disk 200 SSD"
    }
}