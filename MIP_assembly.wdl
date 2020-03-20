workflow MIP_assembly {

    File Sample_Path_List
    String Fastq1_Extension
    String Fastq2_Extension
    Array[Array[String]] SamplesPaths = read_tsv(Sample_Path_List)
    scatter (pair in SamplesPaths){

        String SampleDir = pair[1]
        String sample = pair[0]
        File F1 = SampleDir + sample + Fastq1_Extension
        File F2 = SampleDir + sample + Fastq2_Extension

        call qcAdapters {
            input: 
            sample=sample, 
            file1=F1, 
            file2=F2
        }
        call qcQualityHuman {
            input: 
            sample=sample, 
            file1=qcAdapters.fileR1, 
            file2=qcAdapters.fileR2
        }
        call assemble {
            input: 
            sample=sample, 
            r1=qcQualityHuman.fileR1, 
            r2=qcQualityHuman.fileR2, 
            s1=qcQualityHuman.fileS1, 
            s2=qcQualityHuman.fileS2
        }

        call predictgenes {
            input: 
            sample=sample, 
            fileContigs=assemble.fileContigs
        }

        call map_to_contigs { 
            input: 
            fileR1=qcQualityHuman.fileR1,
            fileR2=qcQualityHuman.fileR2,
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

    call cluster_genes { 
        input: 
        genepredictions=predictgenes.fileFNA 
    }

    Array[Pair[File, File]] fileR1R2 = zip(qcQualityHuman.fileR1, qcQualityHuman.fileR2) 
    
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
        disks: "local-disk 40 SSD"
    }
}

task qcQualityHuman {
    File file1
    File file2
    String sample
    File ref1
    File ref2
    File ref3
    File ref4
    File ref5
    File ref6

    command {
        kneaddata --input ${file1} --input ${file2} -o . \
        -db tools-rx/DATABASES/HG19 --trimmomatic-options "HEADCROP:15 SLIDINGWINDOW:4:15 MINLEN:50" -t 4
        rm *trimmed*
        rm *bowtie2*
        
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
    }
    
    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:070318"
        cpu: 4
        memory: "24GB"
        preemptible: 2
        disks: "local-disk 501 SSD"
    }
}

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
    }
    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:081518"
        cpu: 4
        memory: "15GB"
        preemptible: 2
        disks: "local-disk 100 SSD"
    }
}

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
        disks: "local-disk 100 SSD"
    }
}

task map_to_contigs {
    File fileR1
    File fileR2
    String sample
    File contigs

    command {
        
        bwa index ${contigs}
        samtools faidx ${contigs}

        bwa mem -t 8 -M ${contigs} ${fileR1} ${fileR2} | \
        samtools view - -h -Su -F 2308 -q 0 | \
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
        bootDiskSizeGb: 50
        disks: "local-disk 200 SSD"
    }
}

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
        bootDiskSizeGb: 50
        disks: "local-disk 100 SSD"
    }
}

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
        maxRetries: 2
        disks: "local-disk 100 HDD"
    }
}

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
        maxRetries: 2
        bootDiskSizeGb: 50
        disks: "local-disk 100 SSD"
    }
}

task cluster_genes {
    Array[File] genepredictions

    command {
        cat ${sep=' ' genepredictions} > combined_genepredictions.fna

        usearch8.1.1861_i86linux64 -sortbylength combined_genepredictions.fna -fastaout combined_genepredictions.sorted.fna -minseqlength 102
        cd-hit-est -i combined_genepredictions.sorted.fna -T 32 -aS 0.9 -c 0.95 -M 0 -r 0 -B 0 -d 0 -o nr.fa
        bwa index nr.fa
        samtools faidx nr.fa
    }

    output { 
        File combined_genepredictions = "combined_genepredictions.sorted.fna" 
        File nrFa = "nr.fa"
        File nrFai = "nr.fa.fai"
        File nrRef1 = "nr.fa.bwt"
        File nrRef2 = "nr.fa.pac"
        File nrRef3 = "nr.fa.ann"
        File nrRef4 = "nr.fa.amb"
        File nrRef5 = "nr.fa.sa"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:082018"
        cpu: 32
        memory: "120GB"
        bootDiskSizeGb: 50
        disks: "local-disk 500 SSD"
    }
}

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

        samtools flagstat ${sample}.sort.filtered.ID95.bam > ${sample}.ID95.flagstat.txt

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
        bootDiskSizeGb: 50
        disks: "local-disk 200 SSD"
    }
}
