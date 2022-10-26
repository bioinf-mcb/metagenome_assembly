from _utils import (
    modify_concurrency_config, 
    read_evaluate_log,
    get_files_with_extension,
    check_inputs_not_empty,
    start_workflow,
    write_inputs_file,
    retrieve_config_paths,
    prepare_system_variables
)

import argparse
# Command line argyments
parser = argparse.ArgumentParser(description='Predict genes using Prodigal', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-c','--contig_folder', help='The directory with contigs in .fa format.', required=True)
parser.add_argument('-b','--bins_folder', help='The directory with bins produced by MetaBAT2.', required=True)
parser.add_argument('-g','--gtdbtk_folder', help='The directory with GTDB-tk output.', required=True)
parser.add_argument('-cm','--checkm_folder', help='The directory with CheckM output.', required=True)
parser.add_argument('-gcf', '--gene_cluster_file', help='The file with gene clusters.', required=True)
parser.add_argument('-gc', '--gene_catalog', help='The file with gene catalog.', required=True)
parser.add_argument('-ea', '--eggnog_annotation', help='The file with eggNOG protein annotation.', required=True)
parser.add_argument('-dfa','--deepfri_annotation', help='The file with DeepFRI protein annotation.', required=True) 

parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)
    
# collect contigs from dir
contigs =  get_files_with_extension(args["contig_folder"], ".fa")
bins =  get_files_with_extension(args["bins_folder"], ".bins.tar.gz")
gtdbtk =  get_files_with_extension(args["gtdbtk_folder"], ".bac120.summary.tsv")
checkm =  get_files_with_extension(args["checkm_folder"], "checkm.txt")
eggnog = get_files_with_extension(args["eggnog_annotation"], ".emapper.annotations")
deepfri = get_files_with_extension(args["deepfri_annotation"], "deepfri_annotations.csv")

template["generate_table.genes_to_mags_mapping.gene_clusters"] = args["gene_cluster_file"]
template["generate_table.genes_to_mags_mapping.gene_catalog"] = args["gene_catalog"]
template["generate_table.genes_to_mags_mapping.metabat2_bins"] = bins
template["generate_table.genes_to_mags_mapping.contigs"] = contigs
template["generate_table.genes_to_mags_mapping.gtdbtk_output"] = gtdbtk
template["generate_table.genes_to_mags_mapping.checkm_output"] = checkm
template["generate_table.merge_eggnog_outputs.eggnog_output_files"] = eggnog
template["generate_table.merge_deepfri_outputs.deepfri_output_files"] = deepfri


# writing input json
inputs_path = write_inputs_file(template, system_folder, "_".join(["inputs", script_name]) + ".json")

# check inputs
check_inputs_not_empty({"contigs" : contigs, 
                        "bins" : bins,
                        "gtdbtk" : gtdbtk,
                        "checkm" : checkm,
                        "eggnog" : eggnog,
                        "deepfri" : deepfri})

paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

# modifying config to change number of concurrent jobs and mount dbs
paths["db_mount_config"] = modify_concurrency_config(paths["db_mount_config"], 
                                                     system_folder, 
                                                     n_jobs=1)

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

# checking if the job was successful
read_evaluate_log(log_path)