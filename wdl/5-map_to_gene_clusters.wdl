workflow map_to_gene_clusters {
    Int preemptible_tries

    call map_to_gene_clusters_kma {
        input:
        num_preemtible=preemptible_tries
    }

}

task map_to_gene_clusters_kma {
    File fileR1
    File fileR2
    String sample
    File kma_db
    Int kma_memory_gb
    Int kma_cores
    Int num_preemtible

    command {

        tar -xf ${kma_db}
        kma -ipe ${fileR1} ${fileR2} \
          -o ${sample}.kma \
          -t_db kma_db/nr_db \
          -1t1 \
          -ef \
          -tmp kma_tmp \
          -t ${kma_cores}

        python3 /app/Normalize_kma_output.py --input_file ${sample}.kma.res --out_file ${sample}.geneCPM.txt
    }

    output {
        File kma_output = "${sample}.kma.res"
        File gene_cpm = "${sample}.geneCPM.txt"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/kma:v1.2.27"
        cpu: kma_cores * 2
        memory: kma_memory_gb + "GB"
        preemptible: num_preemtible
        maxRetries: num_preemtible + 1
        disks: "local-disk 200 HDD"
    }
}