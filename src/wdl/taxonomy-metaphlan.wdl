version 1.0 

import "structs.wdl" alias QcFull as SampleInfo

workflow metaphlan {
    input {
    Array[SampleInfo] sampleInfo
    Int thread_num = 4
    
    String sample_suffix = "_paired_1.fastq.gz"
    }

 scatter (info in sampleInfo) {
    call run_metaphlan {
        input:
        fastq_r1=info.paired_r1,
        fastq_r2=info.paired_r2,
        fastq_s1=info.unpaired_r1,
        fastq_s2=info.unpaired_r2,
        sample_id=sub(basename(info.paired_r1), sample_suffix, ""),
        thread=thread_num
        }
    }
}

task run_metaphlan {
    input {
    File fastq_r1
    File fastq_r2
    File fastq_s1
    File fastq_s2
    String sample_id
    Int thread
    }
    
 command {
  
      metaphlan ${fastq_r1},${fastq_r2},${fastq_s1},${fastq_s2} \
                --input_type fastq \
                --add_viruses \
                --unknown_estimation \
                --samout ${sample_id}.sam \
                --bowtie2out ${sample_id}.bowtie2.out \
                --nproc ${thread} \
                -o ${sample_id}.metaphlan.tsv

   samtools view -bS ${sample_id}.sam -o ${sample_id}.bam
   gzip ${sample_id}.bowtie2.out
    }
    
    output {
     File metaphlan_out_tsv = "${sample_id}.metaphlan.tsv"
     File metaphlan_out_bam = "${sample_id}.bam"
     File metaphlan_out_bowtie2 = "${sample_id}.bowtie2.out.gz"
    }
 
 runtime {
  docker: "crusher083/metaphlan@sha256:fd15252fe0ddddff794d3bd60842d54d77796b10344d001163c60ebf8a3c4f75"
        maxRetries: 1
 }

}
