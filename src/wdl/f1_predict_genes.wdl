version 1.0 

workflow predict_mags {
    input { 
    Array[File] contigs
    String sample_suffix = ".min500.contigs.fa"
    }
    
    scatter  (contig in contigs) {
        call predictgenes {
            input:
            contig = contig,
            sample = basename(contig, sample_suffix)
            }
    }
}

task predictgenes {
    input {
    File contig
    String sample
    }
    
    command <<<
        mkdir prodigal
        if [[ `wc -l ~{contig} | awk '{print $1}'` == "0" ]]; then
            touch ~{sample}.gff
            touch ~{sample}.fna
            touch ~{sample}.faa
        else
            prodigal -p meta -i ~{contig} -f gff \
            -o ~{sample}.gff \
            -d ~{sample}.fna \
            -a ~{sample}.faa \
            2> prodigal.stderr > prodigal/prodigal.out
        fi
    >>>
    
    output {
        File fileFNA = "${sample}.fna"
        File fileFAA = "${sample}.faa"
        File fileGFF = "${sample}.gff"
    }

    runtime {
        docker: "crusher083/checkm@sha256:1d5f7508ecf17652dfcaacfe2478c9d330911e44ad4d262a32d1625e9ab2de6b" # docker with prodigal needed
        maxRetries: 1
    }
}