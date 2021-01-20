workflow generate_master_annotation_table {
    Int preemptible_tries

    call merge_eggnog_outputs {
        input:
        num_preemptible=preemptible_tries
    }

    call merge_deepfri_outputs {
        input:
        num_preemptible=preemptible_tries
    }

    call genes_to_mags_mapping {
        input:
        eggnog_annotations=merge_eggnog_outputs.eggnog_table,
        num_preemptible=preemptible_tries
    }
}

task merge_eggnog_outputs {
    Array[File] eggnog_output_files
    Int num_preemptible

    command {

        head -n 1 eggnog_output_files[1] > merged_eggnog_output.tsv
        cat ${write_lines(eggnog_output_files)} > eggnog_output.txt
        while read eggnog_file; do
            tail -n+2 $eggnog_file >> merged_eggnog_output.tsv
        done <eggnog_output.txt
    }

    output {
        File eggnog_table = "merged_eggnog_output.tsv"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/gene-mapper:111920"
        cpu: 2
        memory: "4GB"
        preemptible: num_preemptible
        maxRetries: num_preemptible + 1
        bootDiskSizeGb: 50
        disks: "local-disk 200 HDD"
    }
}

task merge_deepfri_outputs {
    Array[File] deepfri_output_files
    Int num_preemptible

    command {

        head -n 1 deepfri_output_files[1] > merged_deepfri_output.tsv
        cat ${write_lines(deepfri_output_files)} > deepfri_output.txt
        while read deepfri_file; do
            tail -n+2 $deepfri_file >> merged_deepfri_output.tsv
        done <deepfri_output.txt
    }

    output {
        File deepfri_table = "merged_deepfri_output.tsv"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/gene-mapper:111920"
        cpu: 2
        memory: "4GB"
        preemptible: num_preemptible
        maxRetries: num_preemptible + 1
        bootDiskSizeGb: 50
        disks: "local-disk 200 HDD"
    }
}


task genes_to_mags_mapping {
    Array[File] contigs
    File gene_catalogue
    File gene_clusters
    File eggnog_annotations
    Array[File] metabat2_bins
    Array[File] gtdbtk_output
    Array[File] checkm_output
    Int num_preemptible
    Int gene_mapper_memory_gb
    Int gene_mapper_disk_gb

    command {

        # concatenate contigs together to merged_min500.contigs.fa
        cat ${write_lines(contigs)} > contig_fasta.txt
        while read fasta_file; do
            cat $fasta_file >> merged_min500.contigs.fa
        done <contig_fasta.txt

        # extract MAGs to directory 'bins'
        mkdir bins
        cat ${write_lines(metabat2_bins)} > metabat2_bins.txt
        while read bin_file; do
            tar -xf $bin_file -C bins/
        done <metabat2_bins.txt

        # copy GTDBTk output summaries to directory gtdbtk
        mkdir gtdbtk
        cat ${write_lines(gtdbtk_output)} > gtdbtk_2_download.txt
        while read gtdbtk_file; do
            cp $gtdbtk_file gtdbtk/
        done <gtdbtk_2_download.txt

        # copy CheckM output summaries to directory checkm
        mkdir checkm
        cat ${write_lines(checkm_output)} > checkm_2_download.txt
        while read checkm_file; do
            cp $checkm_file checkm/
        done <checkm_2_download.txt

        python3 /app/genes_MAGS_eggNOG_mapping.py \
            --genes_file ${gene_catalogue} \
            --cluster_file ${gene_clusters} \
            --contigs_file merged_min500.contigs.fa \
            --eggnog_ann_file ${eggnog_annotations} \
            --bin_fp bins \
            --tax_fp gtdbtk \
            --checkm_fp checkm \
            --out_gene_mapping_file gene_mapping.tsv \
            --out_cluster_taxa_file gene_clusters_taxa.tsv

    }
    
    output {
        File gene_mag_mappings = "gene_mapping.tsv"
        File gene_cluster_taxa_mappings = "gene_clusters_taxa.tsv"
    }
    
    runtime {
        docker: "gcr.io/microbiome-xavier/gene-mapper:121520"
        cpu: 2
        memory: gene_mapper_memory_gb + "GB"
        preemptible: num_preemptible
        maxRetries: num_preemptible + 1
        bootDiskSizeGb: 50
        disks: "local disk " + gene_mapper_disk_gb + " HDD"
    }
}
