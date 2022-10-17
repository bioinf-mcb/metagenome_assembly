import os 
import json 

from _utils import (
    modify_concurrency_config,
    read_evaluate_log,
    find_database,
    download_database,
    check_inputs_not_empty,
    start_workflow, 
    prepare_system_variables,
    write_inputs_file,
    retrieve_config_paths
)

import argparse

def concatenate_eggnog_database_link(base_url:str, version:str, database:str) -> str:
    return os.path.join(base_url+version, database)

# Command line argyments
parser = argparse.ArgumentParser(description='Qunatify gene abundance mapping genes from catalog to a reference genomes using KMA.', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--input_folder', help='The directory with gene catalog split into chunks', required=True)
parser.add_argument('-db','--eggnog_database', help='Path to a diretory with eggNOG-mapper database', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)
parser.add_argument('-s','--suffix', help='Suffix for the gene catalog chunks', 
                    type=str, default=".fa", required=False)
parser.add_argument('-t','--threads', help='Number of threads to use for clustering', 
                    type=int, default=1, required=False)
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel. Careful, DeepFRI requires around 55GB of RAM per job.', 
                    type=int, default=1, required=False)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)

# eggnog db
eggnog_filename = [".".join(config["eggnog_db"].split(".")[:-1])]
eggnog_path = find_database(args["eggnog_database"], eggnog_filename, "eggNOG")
if not eggnog_path:
    description = "A database of orthology relationships, functional annotation, \
                  and gene evolutionary histories."
    eggnog_db_url = concatenate_eggnog_database_link(config["eggnog_base_url"], config["eggnog_db_version"], 
                                                     config["eggnog_db"])

    eggnog_folder = download_database(args["eggnog_database"], eggnog_db_url, 
                                      "eggNOG", description)

    eggnog_path = find_database(args["eggnog_database"], eggnog_filename, "eggNOG")

# diamond db
diamond_filename = [".".join(config["eggnog_diamond_db"].split(".")[:-1])]
diamond_path = find_database(args["eggnog_database"], diamond_filename, "Diamond")
if not diamond_path:
    description = ""
    diamond_db_url = concatenate_eggnog_database_link(config["eggnog_base_url"], config["eggnog_db_version"], 
                                                     config["eggnog_diamond_db"])

    diamond_folder = download_database(args["eggnog_database"], diamond_db_url, 
                                      "Diamond", description
                                      )

    diamond_path = find_database(args["eggnog_database"], diamond_filename, "Diamond")

# collect files from dir
files =  [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(args["suffix"])]
check_inputs_not_empty({"gene catalog chunks": files})
template["annotate_gene_catalog.gene_clusters_split"] = files
template["annotate_gene_catalog.thread_num"] = args["threads"]

# writing input json
inputs_path = write_inputs_file(template, system_folder, "_".join(["inputs", script_name]) + ".json")

paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

# modifying config to change number of concurrent jobs and mount dbs
paths["config_path"] = modify_concurrency_config(paths["config_path"], system_folder, n_jobs=args["concurrent_jobs"],
                                                 eggnog_path=os.path.abspath(args["eggnog_database"]),
                                                 )

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

read_evaluate_log(log_path)