version 1.0 

<<<<<<< HEAD
import "structs.wdl" alias PairedSample as SampleInfo

workflow qc_and_assemble {
    input {
    Array[SampleInfo] sampleInfo
    Int thread_num = 4
    }
    
    scatter (info in sampleInfo) {
    call kneadData {
        input:
        file_r1=info.file_r1,
        file_r2=info.file_r2,
        sample_id=sub(basename(info.file_r1), "_1.fastq.gz", ""),
        thread=thread_num
        }
=======
    call qcAdapters {
        input: 
        sample_id=sample_id
    }

    call kneadData {
        input: 
        file1=qcAdapters.fileR1, 
        file2=qcAdapters.fileR2,
        sample_id=sample_id
>>>>>>> parent of 91dfb98... Remove trim-galore from QC

    call assemble {
        input:
        r1=kneadData.fileR1, 
        r2=kneadData.fileR2, 
        s1=kneadData.fileS1, 
<<<<<<< HEAD
        s2=kneadData.fileS2,
        sample_id=sub(basename(info.file_r1), "_1.fastq.gz", ""),
        thread=thread_num
        }
=======
        s2=kneadData.fileS2
>>>>>>> parent of 91dfb98... Remove trim-galore from QC
    }
    output {
        Array[File] R1_paired_postqc = kneadData.fileR1
        Array[File] R2_paired_postqc = kneadData.fileR2
        Array[File] S1_unpaired_postqc = kneadData.fileS1
        Array[File] S2_unpaired_postqc = kneadData.fileS2
        Array[File] kneaddata_log = kneadData.log_file
        Array[File] assembled_contigs = assemble.fileContigs
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
    input{
    File file_r1
    File file_r2
    String sample_id
    Int thread
    }
    
    command {
        kneaddata --input ${file_r1} \
                  --input ${file_r2} \
                  -o . \
                  --output-prefix ${sample_id} \
                  -db /GRCh38 \
                  --trimmomatic /app/Trimmomatic/0.39 \
                  --trimmomatic-options "HEADCROP:15 SLIDINGWINDOW:4:15 MINLEN:50" \
                  -t ${thread} \
                  --bowtie2 /bin \
                  --trf /bin \
                  --reorder \
                  --log ${sample_id}.log

        pigz -p ${thread} ${sample_id}_paired_1.fastq
        pigz -p ${thread} ${sample_id}_paired_2.fastq
        pigz -p ${thread} ${sample_id}_unmatched_1.fastq
        pigz -p ${thread} ${sample_id}_unmatched_2.fastq
    }
    
    output {
        File fileR1 = "${sample_id}_paired_1.fastq.gz"
        File fileR2 = "${sample_id}_paired_2.fastq.gz"
        File fileS1 = "${sample_id}_unmatched_1.fastq.gz"
        File fileS2 = "${sample_id}_unmatched_2.fastq.gz"
        File log_file = "${sample_id}.log"
    }

    runtime {
        docker: "crusher083/kneaddata@sha256:79af69ef6fa899c97e4e075599e75a85b299af1c6301143ca21f9025041fb68f" # use kneaddata docker here
        maxRetries: 1
    }
}


task assemble {
    input{
    # input sequences
    File r1
    File r2 
    File s1 
    File s2
<<<<<<< HEAD
    # sample id 
    String sample_id
    # parameter
    Int thread
    }
    # tilde syntax should be used with <<<>>> 
    # https://github.com/openwdl/wdl/blob/main/versions/1.0/SPEC.md --> Command Section
    command <<< 
        megahit -1 ~{r1} -2 ~{r2} -r ~{s1},~{s2} -t ~{thread} -m 0.6 -o assemble
        cat assemble/final.contigs.fa | \
        awk -v var="~{sample_id}" '
            {if($0 ~ /^>/) {contigName=substr($0, 2,length($0))} 
            else {seq=$0; if(length($0) >= 500) {print ">"var"_"contigName"\n"seq}} }' > assemble/~{sample_id}.min500.contigs.fa
    >>>

    output {
        File fileContigs = "assemble/${sample_id}.min500.contigs.fa"
    }   
    
    runtime {
        docker: "crusher083/megahit@sha256:a37cb37b44c58a09ba122ccfa797cb6dfd0fac54c173abab02ccbf12c62f1f94"
        maxRetries: 1
=======
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
>>>>>>> parent of 91dfb98... Remove trim-galore from QC
    }
}
