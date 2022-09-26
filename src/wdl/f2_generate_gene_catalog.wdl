version 1.0

workflow generate_gene_catalog {
    input { 
    Array[File] genepreds
    Int thread_num = 32
    }
    
    call cluster_genes {
        input:
        genepredictions = genepreds,
        threads = thread_num
    }
    call kma_index {
        input:
        nr=cluster_genes.nrFa
    }
}

task cluster_genes {
    input{
    Array[File] genepredictions
    Int threads
    }
    
    command <<<
        cat ~{sep=' ' genepredictions} > combined_genepredictions.fna
        /app/extract_complete_gene.py combined_genepredictions.fna > combined_genepredictions.complete.fna

        # note: no de-replication done here since this would exclude linkage between a part of the genes and MAGs

        usearch11.0.667_i86linux32 \
          -sortbylength combined_genepredictions.complete.fna \
          -fastaout combined_genepredictions.sorted.fna \
          -minseqlength 1

        cd-hit-est -i combined_genepredictions.sorted.fna -T ~{threads} -aS 0.9 -c 0.95 -M 0 -r 0 -B 0 -d 0 -o nr.fa

        # split nr.fa into files with 10,000 sequences each
        awk 'BEGIN {n_seq=0;n_file=1} /^>/ {if(n_seq%10000==0){file=sprintf("nr_%d.fa",n_file);n_file++} print >> file; n_seq++; next;} { print >> file; }' < nr.fa
    >>>

    output { 
        File combined_genepredictions = "combined_genepredictions.sorted.fna" 
        File nrFa = "nr.fa"
        File nrClusters = "nr.fa.clstr"
    }

    runtime {
        docker: "crusher083/gene-clustering@sha256:4201851cdf8f451ada6a4833f2441f54730e7d7f29f988b6b4a5312ac899a483" # use docker gene_clustering
        maxRetries: 1
    }
}

task kma_index {
    input{
    File nr
    }
    
    command {

        mkdir kma_db
        kma index -i ${nr} -o kma_db/nr_db
        tar -zcf kma_db.tar.gz kma_db/*

    }

    output {
        File kma_db = "kma_db.tar.gz"
    }

    runtime {
        docker: "crusher083/kma@sha256:917f1889054df58b6a2e631d6187ed9db81d0f415b7a150ed1222d414d68e1c6"
        maxRetries: 1
    }
}