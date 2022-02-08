version 1.0 

import "structs.wdl" alias PairedSample as SampleInfo

workflow map_to_gene_clusters {
    input { 
    Array[SampleInfo] sampleInfo
    File kma_db_file
    Int thread_num = 15
    String sample_suffix = "paired_1.fastq.gz"
    }
    
    scatter (info in sampleInfo) {
    call map_to_gene_clusters_kma {
        input:
        fileR1=info.file_r1,
        fileR2=info.file_r2,
        sample=sub(basename(info.file_r1), sample_suffix, ""),
        kma_db = kma_db_file,
        threads=thread_num
        }
    }
}

task map_to_gene_clusters_kma {
    input {
    File fileR1
    File fileR2
    String sample
    File kma_db
    Int threads
    }
    
    command {
        # TODO: mount kma_db as volume to Docker
        tar --use-compress-program=pigz -xf ${kma_db}
        kma -ipe ${fileR1} ${fileR2} \
          -o ${sample}.kma  \
          -t_db kma_db/nr_db \
          -1t1 \
          -ef \
          -t ${threads}

        python3 /app/Normalize_kma_output.py --input_file ${sample}.kma.res --out_file ${sample}.geneCPM.txt
    }

    output {
        File kma_output = "${sample}.kma.res"
        File gene_cpm = "${sample}.geneCPM.txt"
    }

    runtime {
        docker: "crusher083/kma@sha256:86c5237a5c7a9caf06acff4ce0cd42f913081ecb19853d70bbcf70f4f94de0fd"
        maxRetries: 1
    }
}