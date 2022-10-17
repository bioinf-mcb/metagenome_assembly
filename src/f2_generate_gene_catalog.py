import os 

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
parser = argparse.ArgumentParser(description='Cluster genes predicted by Prodigal into gene catalog.', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--input_folder', help='The directory with predicted genes in .fna format', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)
parser.add_argument('-s','--suffix', help='Suffix of the filename to be identified in input folder & replaced in the output(i.e. -s .fa  -i ID7.fa -> ID7.fna)', 
                    type=str, default=".fna")
parser.add_argument('-t','--threads', help='Number of threads to use for clustering', 
                    type=int, default=1, required=False)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)
    
# collect files from dir
files =  get_files_with_extension(args["input_folder"], args["suffix"])
check_inputs_not_empty({"gene predictions" : files})
template["generate_gene_catalog.genepreds"] = files
template["generate_gene_catalog.thread_num"] = args["threads"]

# writing input json
inputs_path = write_inputs_file(template, system_folder, "_".join(["inputs", script_name]) + ".json")

paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

# modifying config to change number of concurrent jobs and mount dbs
paths["db_mount_config"] = modify_concurrency_config(paths["db_mount_config"], system_folder, n_jobs=1)

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

read_evaluate_log(log_path)

# rename output folder
glob_name = [file for file in os.listdir(args["output_folder"]) if file.startswith("glob")][0]
os.rename(os.path.join(args["output_folder"], glob_name), os.path.join(args["output_folder"], "gene_catalog_split"))