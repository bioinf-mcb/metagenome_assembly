workflow predict_mags {

    call predictgenes 

    call map_to_contigs 

    call metabat2 {
        input:
        bam=map_to_contigs.fileBAM
    }

    call checkm {
        input:
        bins=metabat2.bins,
    }

    call gtdbtk {
        input:
        bins=metabat2.bins,
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
        docker: "crusher083/metabat2@sha256:sha256:f5a6a59608c3a77a30eac2887d694e1b6cfef904bec361cd18e500188dfc848e" # docker with prodigal needed
        cpu: 1
        memory: "7GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 100 SSD"
    }
}

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
        docker: "crusher083/metabat2@sha256:sha256:f5a6a59608c3a77a30eac2887d694e1b6cfef904bec361cd18e500188dfc848e" # docker with bwa and samtools needed
        cpu: 8
        memory: "24GB"
        preemptible: 2
        maxRetries: 3
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
        docker: "crusher083/metabat2@sha256:sha256:f5a6a59608c3a77a30eac2887d694e1b6cfef904bec361cd18e500188dfc848e" 
        cpu: 8
        memory: "12GB"
        preemptible: 2
        maxRetries: 3
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
        docker: "crusher083/metabat2@sha256:sha256:f5a6a59608c3a77a30eac2887d694e1b6cfef904bec361cd18e500188dfc848e" 
        cpu: 4
        memory: "100GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 100 HDD"
    }
}

task gtdbtk {
    File bins
    File gtdb_reference
    String gtdb_release
    String sample

    command {

        export GTDBTK_DATA_PATH=/gtdbtk-data/${gtdb_release}/
        tar -xf ${bins}
        gtdbtk classify_wf --genome_dir ${sample}_bins/ -x fa --cpus 4 --out_dir ${sample}_gtdb
        tar -czf ${sample}_gtdb.tar.gz ${sample}_gtdb

        if [[ -e ${sample}_gtdb/classify/gtdbtk.bac120.summary.tsv ]]
        then
          cp ${sample}_gtdb/classify/gtdbtk.bac120.summary.tsv ${sample}.bac120.summary.tsv
        else
          touch ${sample}.bac120.summary.tsv
        fi

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
