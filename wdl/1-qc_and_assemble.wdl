workflow qc_and_assemble {
    String sample_id

    call qcAdapters {
        input: 
        sample_id=sample_id
    }

    call kneadData {
        input: 
        file1=qcAdapters.fileR1, 
        file2=qcAdapters.fileR2,
        sample_id=sample_id

    call assemble {
        input: 
        r1=kneadData.fileR1, 
        r2=kneadData.fileR2, 
        s1=kneadData.fileS1, 
        s2=kneadData.fileS2
    }

    output {
        File R1_paired_postqc = kneadData.fileR1
        File R2_paired_postqc = kneadData.fileR2
        File S1_unpaired_postqc = kneadData.fileS1
        File S2_unpaired_postqc = kneadData.fileS2
        File kneaddata_log = kneadData.log_file
        File assembled_contigs = assemble.fileContigs
    }

}

task qcAdapters {
    File file1
    File file2
    String sample_id

    command {

        # move file into name that fits with the sample naming strategy
        mv ${file1} ${sample_id}.1.fq.gz
        mv ${file2} ${sample_id}.2.fq.gz

        trim_galore --paired --phred33 --quality 0 --stringency 5 --length 10 \
        ${sample_id}.1.fq.gz ${sample_id}.2.fq.gz

        mv ${sample_id}.1_val_1.fq.gz ${sample_id}.adapterTrimmed.1.fq.gz
        mv ${sample_id}.2_val_2.fq.gz ${sample_id}.adapterTrimmed.2.fq.gz
    }
    
    output {
        File fileR1 = "${sample_id}.adapterTrimmed.1.fq.gz"
        File fileR2 = "${sample_id}.adapterTrimmed.2.fq.gz"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:070318" # docker with trim galore needed
        cpu: 1
        memory: "1GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 40 SSD"
    }
}


task kneadData {
    File file_r1
    File file_r2
    String sample_id

    command {
        kneaddata --input ${file_r1} \
                  --input ${file_r2} \
                  -o . \
                  --output-prefix ${sample_id} \
                  -db /hg37 \
                  --trimmomatic-options "HEADCROP:15 SLIDINGWINDOW:4:15 MINLEN:50" \
                  -t 4 \
                  --reorder \
                  --remove-intermediate-output \
                  --trimmomatic /opt/conda/share/trimmomatic \
                  --log ${sample_id}.log

        rm *bowtie2*

        gzip ${sample_id}_paired_1.fastq
        gzip ${sample_id}_paired_2.fastq
        gzip ${sample_id}_unmatched_1.fastq
        gzip ${sample_id}_unmatched_2.fastq
    }
    
    output {
        File fileR1 = "${sample_id}.adapterTrimmed.1_kneaddata_paired_1.fastq.gz"
        File fileR2 = "${sample_id}.adapterTrimmed.1_kneaddata_paired_2.fastq.gz"
        File fileS1 = "${sample_id}.adapterTrimmed.1_kneaddata_unmatched_1.fastq.gz"
        File fileS2 = "${sample_id}.adapterTrimmed.1_kneaddata_unmatched_2.fastq.gz"
        File log_file = "${sample_id}.log"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:101419" # use kneaddata docker here
        cpu: 4
        memory: "24GB"
        preemptible: 2
        maxRetries: 3
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
    
}   runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:081518" # metahit docker as in 1_2-assemble.wdl
        cpu: 4
        memory: "15GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 100 SSD"
    }
}
