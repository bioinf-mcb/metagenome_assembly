workflow generate_table {

    call merge_eggnog_outputs {
    }

    call merge_deepfri_outputs {
    }

    call genes_to_mags_mapping {
        input:
        eggnog_annotations=merge_eggnog_outputs.eggnog_table,
    }
}

task merge_eggnog_outputs {
    Array[File] eggnog_output_files

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
        docker: "crusher083/gene-mapper@sha256:621db5845d6204cf0bb7b67163c7adc068d0fc91dcdcb20e7670703277be71e4"
    }
}

task merge_deepfri_outputs {
    Array[File] deepfri_output_files

    command {

        head -n 1 deepfri_output_files[1] > merged_deepfri_output.tsv
        cat ${write_lines(deepfri_output_files)} > deepfri_output.txt
        while read deepfri_file; do
            tail -n+2 $deepfri_file >> merged_deepfri_output.tsv
        done < deepfri_output.txt
    }

    output {
        File deepfri_table = "merged_deepfri_output.tsv"
    }

    runtime {
        docker: "crusher083/gene-mapper@sha256:621db5845d6204cf0bb7b67163c7adc068d0fc91dcdcb20e7670703277be71e4"
    }
}


task genes_to_mags_mapping {
    Array[File] contigs
    File gene_catalog
    File gene_clusters
    File eggnog_annotations
    Array[File] metabat2_bins
    Array[File] gtdbtk_output
    Array[File] checkm_output

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
            --genes_file ${gene_catalog} \
            --cluster_file ${gene_clusters} \
            --contigs_file merged_min500.contigs.fa \
            --eggnog_ann_file ${eggnog_annotations} \
            --bin_fp bins \
            --tax_fp gtdbtk \
            --checkm_fp checkm \
            --out_path . \
            --split-output \
            --out_name ""

    }
    
    output {
        File gene_cluster_info = "_mapped_genes_cluster.tsv"
        File gene_info = "_individual_mapped_genes.tsv"
        File MAG_info = "_MAGS.tsv"
    }
    
    runtime {
        docker: "crusher083/gene-mapper@sha256:621db5845d6204cf0bb7b67163c7adc068d0fc91dcdcb20e7670703277be71e4"
    }
}
