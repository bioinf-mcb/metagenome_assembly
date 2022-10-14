version 1.0

workflow annotate_gene_catalog {
    input{
        Array[File] gene_clusters_split
        Int thread_num = 4 
    }
    
    scatter (gene_shard in gene_clusters_split) {

        call annotate_eggnog {
            input:
            gene_catalog=gene_shard,
            eggnog_threads=thread_num
        }

        call annotate_deepfri {
            input:     
            gene_catalog=gene_shard
        }
    }
}

task annotate_eggnog {
    input {
    File gene_catalog
    Int eggnog_threads
    String gene_catalog_name = basename(gene_catalog, ".fa")
    }
    
    command {
        # TODO: mount in submit script 
        
        echo ${gene_catalog_name}
        python3.9 /app/eggnog-mapper-2.1.6/emapper.py \
            --itype CDS \
            --cpu ${eggnog_threads} \
            -i ${gene_catalog} \
            --output nr-eggnog \
            --output_dir . \
            -m diamond \
            -d none \
            --tax_scope auto \
            --go_evidence non-electronic \
            --target_orthologs all \
            --seed_ortholog_evalue 0.001 \
            --seed_ortholog_score 60 \
            --query_cover 20 \
            --subject_cover 0 \
            --translate \
            --override

        mv nr-eggnog.emapper.annotations ${gene_catalog_name}.emapper.annotations
        mv nr-eggnog.emapper.seed_orthologs ${gene_catalog_name}.emapper.seed_orthologs

    }

    output {
        File eggnog_annotations = "${gene_catalog_name}.emapper.annotations"
        File eggnog_seed_orthologs = "${gene_catalog_name}.emapper.seed_orthologs"
    }

    runtime {
        docker: "crusher083/eggnog-mapper@sha256:79301af19fc7af2b125297976674e88a5b4149e1867977938510704d1198f70f"
        maxRetries: 1
    }
}

task annotate_deepfri {
    input {
    File gene_catalog
    String gene_catalog_name = basename(gene_catalog, ".fa")
    } 
    
    command {
        echo ${gene_catalog_name}
        /bin/python3 /app/scripts/cromwell_process_fasta.py -i ${gene_catalog} \
        -o ${gene_catalog_name}_deepfri_annotations.csv -m /app --translate
    }

    output {
        File deepfri_out = "${gene_catalog_name}_deepfri_annotations.csv"
    }

    runtime {
        docker: "crusher083/deepfri_seq@sha256:7d65c3e0d58a6cc38bd55f703a337910499b3d5d76a7330480a6cc391d09ffb6"
        maxRetries: 1
    }
}

