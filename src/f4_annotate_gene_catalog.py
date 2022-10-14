import os 
import json 

from _utils import (
    modify_output_config,
    modify_concurrency_config,
    read_json_config,
    create_directory,
    read_evaluate_log,
    find_database,
    download_database,
    check_inputs_not_empty,
    start_workflow, 
    load_input_template
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



args = vars(parser.parse_args())
system_folder = os.path.join(args["output_folder"], "system")

script_dir = os.path.dirname(__file__)
config = read_json_config(os.path.join(script_dir, "config.json"))

# eggnog db
eggnog_filename = [".".join(config["eggnog_db"].split(".")[:-1])]
eggnog_path = find_database(args["eggnog_database"], eggnog_filename, "eggNOG")
if not eggnog_path:
    description = "A database of orthology relationships, functional annotation, \
                  and gene evolutionary histories."
    eggnog_db_url = concatenate_eggnog_database_link(config["eggnog_base_url"], config["eggnog_db_version"], 
                                                     config["eggnog_db"])

    eggnog_folder = download_database(args["eggnog_database"], eggnog_db_url, 
                                      "eggNOG", description
                                      )

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

# Getting necessary files from script name
script_name = os.path.basename(__file__).split(".")[0]

# load input template
template = load_input_template(script_dir, script_name, config)

# collect files from dir
files =  [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(args["suffix"])]
check_inputs_not_empty({"gene catalog chunks": files})
template["annotate_gene_catalog.gene_clusters_split"] = files
template["annotate_gene_catalog.thread_num"] = args["threads"]

# creating output directory
create_directory(args["output_folder"])
create_directory(system_folder)

# writing input json
inputs_path = os.path.join(system_folder, 'input_annotate_catalog.json')

with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)



paths = {
    "config_path" : config["db_mount_config"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"][script_name],
    "output_config_path" : config["output_config_path"]
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

# modifying config to change output folder
paths["output_config_path"] = modify_output_config(paths["output_config_path"], args["output_folder"], system_folder)
# modifying config to change number of concurrent jobs and mount dbs
paths["config_path"] = modify_concurrency_config(paths["config_path"], 
                                                 system_folder,
                                                 eggnog_path=os.path.abspath(args["eggnog_database"]),
                                                 n_jobs=args["concurrent_jobs"])

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder)

read_evaluate_log(log_path)