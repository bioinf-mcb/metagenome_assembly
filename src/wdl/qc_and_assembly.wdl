version 1.0

import "structs.wdl" alias PairedSample as SampleInfo
import "util_kneaddata.wdl" as utils

workflow qc_and_assemble {
    input {
    Array[SampleInfo] sampleInfo
    Int thread_num = 4

    # Trimmomatic params
    String trimmomatic_options = "\"HEADCROP:15 SLIDINGWINDOW:4:15 MINLEN:50\""
    String sequencer_source = "\"NexteraPE\""
    
    # bowtie2 params
    String bowtie2_options = "\"--very-sensitive\""
    
    # Trf params
    Int trf_match = 2
    Int trf_mismatch = 7
    Int trf_delta = 7
    Int trf_pm = 80
    Int trf_pi = 10
    Int trf_minscore = 50
    Int trf_maxperiod = 500
    
    
    }
    
    scatter (info in sampleInfo) {
    
    call kneadData {
        input:
        file_r1=info.file_r1,
        file_r2=info.file_r2,
        sample_id = info.sample_id,
        thread=thread_num,

        trimmomatic_options=trimmomatic_options,
        sequencer_source=sequencer_source,
        
        bowtie2_options=bowtie2_options,
        
        match=trf_match,
        mismatch=trf_mismatch,
        delta=trf_delta,
        pm=trf_pm,
        pi=trf_pi,
        minscore=trf_minscore,
        maxperiod=trf_maxperiod
        }
    
    call assemble {
        input:
        r1=kneadData.fileR1, 
        r2=kneadData.fileR2, 
        s1=kneadData.fileS1, 
        s2=kneadData.fileS2,
        sample_id=info.sample_id,
        thread=thread_num
        }
    }
    call utils.countTable as generateTable {
	    input:
        logFiles = kneadData.log_file
	}
    
    output {
        Array[File]? R1_paired_postqc = kneadData.fileR1
        Array[File]? R2_paired_postqc = kneadData.fileR2
        Array[File]? S1_unpaired_postqc = kneadData.fileS1
        Array[File]? S2_unpaired_postqc = kneadData.fileS2
        Array[File]? kneaddata_log = kneadData.log_file
        Array[File] assembled_contigs = assemble.fileContigs
        File? rc_table = generateTable.kneaddataReadCountTable
    }
}



task kneadData {
    input{
    File file_r1
    File file_r2
    
    String sample_id
    Int thread

    # Trimmomatic parameters
    String trimmomatic_options 
    String sequencer_source
    
    # bowtie2 parameters
    String bowtie2_options 
    
    # Trf params
    Int match 
    Int mismatch
    Int delta 
    Int pm 
    Int pi 
    Int minscore
    Int maxperiod
    }
    
    command {
        kneaddata -i1 ${file_r1} \
                  -i2 ${file_r2} \
                  -o . \
                  --output-prefix ${sample_id} \
                  -db "/GRCh38" \
                  --trimmomatic="/app/Trimmomatic/0.39" \
                  --trimmomatic-options=${trimmomatic_options} \
                  --sequencer-source=${sequencer_source} \
                  --bowtie2 /bin \
                  --bowtie2-options=${bowtie2_options} \
                  --trf /bin \
                  --match ${match} \
                  --mismatch ${mismatch} \
                  --delta ${delta} \
                  --pm ${pm} \
                  --pi ${pi} \
                  --minscore ${minscore} \
                  --maxperiod ${maxperiod} \
                  --reorder \
                  --remove-intermediate-output \
                  --log ${sample_id}.log \
                  -t ${thread} 

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
        docker: "crusher083/kneaddata@sha256:74614fc84f02412f975c66fbee9d02ab211be5974478ac5c3b78b2d7178839d7" # use kneaddata docker here
        maxRetries: 1
    }
}


task assemble {
    input{
    # input sequences
    File r1
    File r2 
    File? s1 
    File? s2

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
        docker: "crusher083/megahit@sha256:daf071c004a26f1ce7fe48a7fb0c573ca7eab4475553ab6e03e45492ac220653"
        maxRetries: 1
        }
}