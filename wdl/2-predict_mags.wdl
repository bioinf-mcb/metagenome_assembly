version 1.0 

import "structs.wdl" alias QcAndContigs as SampleInfo

workflow predict_mags {
    input { 
    Array[SampleInfo] sampleInfo
    Int thread_num = 30
    String sample_suffix = ".min500.contigs.fa"
    String gtdb_release = "release202"
    }
    
    scatter  (info in sampleInfo) {
    call predictgenes {
        input:
        contigs = info.contigs,
        sample = sub(basename(info.contigs), sample_suffix, "")
        }

    call map_to_contigs {
        input:
        fileR1 = info.file_r1,
        fileR2 = info.file_r2,
        contigs = info.contigs,
        sample = sub(basename(info.contigs), sample_suffix, ""),
        thread = thread_num
        }

    call metabat2 {
        input:
        bam=map_to_contigs.fileBAM,
        contigs = info.contigs,
        sample = sub(basename(info.contigs), sample_suffix, "")
        }
    ## TODO: split file right here to prevent GTDB-tk RAM bottleneck
    call checkm {
        input:
        bins=metabat2.bins,
        sample = sub(basename(info.contigs), sample_suffix, ""),
        thread = thread_num
        }

    call gtdbtk {
        input:
        bins=metabat2.bins,
        gtdb_release = gtdb_release,
        sample = sub(basename(info.contigs), sample_suffix, ""),
        thread = thread_num
        }
    }
}


task predictgenes {
    input {
    File contigs
    String sample
    }
    
    command <<<
        mkdir prodigal
        if [[ `wc -l ~{contigs} | awk '{print $1}'` == "0" ]]; then
            touch prodigal/~{sample}.gff
            touch prodigal/~{sample}.fna
            touch prodigal/~{sample}.faa
        else
            prodigal -p meta -i ~{contigs} -f gff \
            -o prodigal/~{sample}.gff \
            -d prodigal/~{sample}.fna \
            -a prodigal/~{sample}.faa \
            2> prodigal/prodigal.stderr > prodigal/prodigal.out
        fi
    >>>
    
    output {
        File fileFNA = "prodigal/${sample}.fna"
        File fileFAA = "prodigal/${sample}.faa"
        File fileGFF = "prodigal/${sample}.gff"
    }

    runtime {
        docker: "crusher083/checkm@sha256:1d5f7508ecf17652dfcaacfe2478c9d330911e44ad4d262a32d1625e9ab2de6b" # docker with prodigal needed
        maxRetries: 1
    }
}

task map_to_contigs {
    input {
    File fileR1
    File fileR2
    File contigs
    String sample
    Int thread
    }
    
    command {
        # indexing contigs file with BWA and Samtools
        bwa index ${contigs}
        samtools faidx ${contigs}

        bwa mem -t ${thread} -M ${contigs} ${fileR1} ${fileR2} | \
        samtools view - -h -Su -F 2308 -q 0 | \
        # sorting BAM file with Samtools
        samtools sort -@ ${thread} -m 2G -O bam -o ${sample}.sort.bam 

    }
    
    output {

        File fileBAM = "${sample}.sort.bam"

    }
    
    runtime {
        docker: "crusher083/bwa-samtools@sha256:bb3bc0f565e1e6d17f3a72fd90fad8536fec282781e6a09e53d950be76f1e359" # docker with bwa and samtools needed
        maxRetries: 1
    }
}

task metabat2 {
    input {
    File bam
    String sample
    File contigs
    }
    
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
        docker: "metabat/metabat@sha256:15d0392bf424922dc6f3ed08e49efc4d48eec4a07f2b075564c94606b14de6fd" 
        maxRetries: 1

    }
}

task checkm {
    input{
    File bins
    String sample
    Int thread
    }
    
    command {

        checkm data setRoot /checkm-data
        tar -xvf ${bins}
        
        # https://github.com/broadinstitute/cromwell/issues/3647
        export TMPDIR=/tmp
        
        checkm lineage_wf -f ${sample}_checkm.txt -t ${thread} -x fa ${sample}_bins/ ${sample}_checkm
        #checkm lineage_wf -t 10 -x fa ${sample}_bins/ ${sample}_checkm
        tar -cf ${sample}_checkm.tar ${sample}_checkm
        gzip ${sample}_checkm.tar

    }

    output {

        File? checkm_summary = "${sample}_checkm.txt"
        File checkm_out = "${sample}_checkm.tar.gz"

    }

    runtime {
        docker: "crusher083/checkm@sha256:1d5f7508ecf17652dfcaacfe2478c9d330911e44ad4d262a32d1625e9ab2de6b" 
        maxRetries: 1
    }
}

task gtdbtk {
    input{
    File bins
    String gtdb_release
    String sample
    Int thread
    } 
    
    command {

        export GTDBTK_DATA_PATH=/gtdbtk-data/${gtdb_release}/
        tar -xf ${bins}        
        
        # https://github.com/broadinstitute/cromwell/issues/3647
        export TMPDIR=/tmp
        
        gtdbtk classify_wf --genome_dir ${sample}_bins/ -x fa --cpus ${thread} --out_dir ${sample}_gtdb
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
        docker: "crusher083/gtdb-tk@sha256:c080f0de4a3a9907a042de9d579a2a3bace9167e704ca7d850303d3986205d70"
        maxRetries: 1
    }
}
