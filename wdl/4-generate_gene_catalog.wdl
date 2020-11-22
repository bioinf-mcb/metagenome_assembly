workflow generate_gene_catalog {
	Int preemptible_tries

    call cluster_genes 

    call kma_index {
        input:
        nr=cluster_genes.nrFa
    }
}

task cluster_genes {
    Array[File] genepredictions

    command <<<
        cat ${sep=' ' genepredictions} > combined_genepredictions.fna
        /app/extract_complete_gene.py combined_genepredictions.fna > combined_genepredictions.complete.fna

        # note: no de-replication done here since this would exclude linkage between a part of the genes and MAGs

        usearch8.1.1861_i86linux64 \
          -sortbylength combined_genepredictions.complete.fna \
          -fastaout combined_genepredictions.sorted.fna \
          -minseqlength 1

        cd-hit-est -i combined_genepredictions.sorted.fna -T 32 -aS 0.9 -c 0.95 -M 0 -r 0 -B 0 -d 0 -o nr.fa

        # split nr.fa into files with 10,000 sequences each
        awk 'BEGIN {n_seq=0;n_file=1} /^>/ {if(n_seq%10000==0){file=sprintf("nr_%d.fa",n_file);n_file++} print >> file; n_seq++; next;} { print >> file; }' < nr.fa
    >>>

    output { 
        File combined_genepredictions = "combined_genepredictions.sorted.fna" 
        File nrFa = "nr.fa"
        File nrClusters = "nr.fa.clstr"
        Array[File] nr_split = glob("nr_*.fa")
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:032819"
        cpu: 32
        memory: "120GB"
        bootDiskSizeGb: 50
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 500 SSD"
    }
}

task kma_index {
    File nr

    command {

        mkdir kma_db
        kma index -i ${nr} -o kma_db/nr_db
        tar -zcf kma_db.tar.gz kma_db/*

    }

    output {
        File kma_db = "kma_db.tar.gz"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/kma:v1.2.27"
        cpu: 4
        memory: "120GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 200 SSD"
    }
}