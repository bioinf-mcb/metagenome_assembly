workflow annotate_gene_catalogue {
    Array[File] gene_clusters_split

    scatter (gene_shard in gene_clusters_split){

        call annotate_eggnog {
            input:
            gene_catalogue=gene_shard 
        }

        call annotate_deepfri {
            input:     
            gene_catalogue=gene_shard
        }
    }
}

task annotate_eggnog {
    File gene_catalogue
    File eggnog_db
    File eggnog_db_diamond
    Int eggnog_memory_gb
    Int eggnog_threads

    command {
        gunzip -c ${eggnog_db} > /app/eggnog-mapper-2.0.1/data/eggnog.db
        gunzip -c ${eggnog_db_diamond} > /app/eggnog-mapper-2.0.1/data/eggnog_proteins.dmnd

        python /app/eggnog-mapper-2.1.6/emapper.py 
            --cpu ${eggnog_num_cores} \
            -i ${gene_catalogue} \
            --output nr-eggnog \
            --output_dir . \
            -m diamond \
            -d none \
            --tax_scope auto \
            --go_evidence non-electronic \
            --target_orthologs all \
            --seed_ortholog_evalue 0.001 \
            --seed_ortholog_score 60 \
            --query-cover 20 \
            --subject-cover 0 \
            --translate \
            --override

    }

    output {
        File eggnog_annotations = "nr-eggnog.emapper.annotations"
        File eggnog_seed_orthologs = "nr-eggnog.emapper.seed_orthologs"
    }

    runtime {
        docker: "crusher083/eggnog-mapper@sha256:f1c1a34523fa2f625be0ae074ae17b4ff493ead88e6b670e4a9e077d25b53ec9 "
        maxRetries: 1
    }
}

task annotate_deepfri {
    File gene_catalogue
    Int deepfri_memory_gb

    command {
        /bin/python3 /app/scripts/cromwell_process_fasta.py -i ${gene_catalogue} -o deepfri_annotations.csv -m /app --translate
    }

    output {
        File deepfri_out = "deepfri_annotations.csv"
    }

    runtime {
        docker: "#DeepFri Docker here"
        maxRetries: 1
    }
}

