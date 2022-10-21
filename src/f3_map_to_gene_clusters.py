from nis import match
import os 
import json 

from _utils import (
    modify_concurrency_config,
    read_evaluate_log, 
    get_files_with_extension,
    reorder_list_substrings,
    check_inputs_not_empty,
    start_workflow,
    write_inputs_file,
    retrieve_config_paths,
    prepare_system_variables
)

import argparse

# Command line argyments
parser = argparse.ArgumentParser(description='Qunatify gene abundance mapping genes from catalog to a reference genomes using KMA.', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--input_folder', help='The directory with reads in fastq.gz format.', required=True)
parser.add_argument('-db','--database', help='Path to KMA database from previous step.', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)
parser.add_argument('-s1','--suffix1', help='Suffix of the first of the paired reads', 
                    type=str, default="_paired_1.fastq.gz", required=False)
parser.add_argument('-s2','--suffix2', help='Suffix of the second of the paired reads', 
                    type=str, default="_paired_2.fastq.gz", required=False)
parser.add_argument('-t','--threads', help='Number of threads to use for clustering', 
                    type=int, default=1, required=False)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)

# collect files from dir
forward = get_files_with_extension(args["input_folder"], args["suffix1"])
reverse = get_files_with_extension(args["input_folder"], args["suffix2"])
reverse = reorder_list_substrings(reverse, [x.split("_")[0] for x in forward])

# modify template
for read_1, read_2 in zip(forward, reverse):
    template["map_to_gene_clusters.sampleInfo"].append({"file_r1": read_1, 
                                                        "file_r2": read_2, 
                                                        "sample_id": read_1.split(args["suffix1"])[0]})

template["map_to_gene_clusters.thread_num"] = args["threads"]
template["map_to_gene_clusters.kma_db_file"] = args["database"]
check_inputs_not_empty({"reads" : template["map_to_gene_clusters.sampleInfo"], 
                        "kma database file": template["map_to_gene_clusters.kma_db_file"]})

template["map_to_gene_clusters.sample_suffix"] = args["suffix1"]

# writing input json
inputs_path = write_inputs_file(template, system_folder, "_".join(["inputs", script_name]) + ".json")

# creating absolute paths
paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

# modifying config to change number of concurrent jobs and mount dbs
paths["db_mount_config"] = modify_concurrency_config(paths["db_mount_config"], system_folder, n_jobs=1)

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

read_evaluate_log(log_path)