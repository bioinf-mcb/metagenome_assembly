import os 
import json 
import sys
from _utils import (
    modify_output_config,
    modify_concurrency_config,
    read_json_config,
    create_directory,
    read_evaluate_log
)

import argparse

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
args["system_folder"] = os.path.join(args["output_folder"], "system")

script_dir = os.path.dirname(__file__)
config = read_json_config(os.path.join(script_dir, "config.json"))

# load input template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "annotate_gene_catalog.json")
with open(template_path) as f:
    template = json.loads(f.read())

# collect files from dir
files =  [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(args["suffix"])]
template["annotate_gene_catalog.gene_clusters_split"] = files
template["annotate_gene_catalog.thread_num"] = args["threads"]

# creating output directory
create_directory(args["output_folder"])
create_directory(args["system_folder"])

# writing input json
inputs_path = os.path.join(args["system_folder"], 'input_map_to_gene_clusters.json')

with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)



paths = {
    "config_path" : config["db_mount_config"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"]["f4_annotate_gene_catalog"],
    "output_config_path" : config["output_config_path"]
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

# modifying config to change output folder
paths["output_config_path"] = modify_output_config(paths["output_config_path"], args["output_folder"], args["system_folder"])
# modifying config to change number of concurrent jobs and mount dbs
paths["config_path"] = modify_concurrency_config(paths["config_path"], 
                                                 args["system_folder"],
                                                 eggnog_path=os.path.abspath(args["eggnog_database"]),
                                                 n_jobs=args["concurrent_jobs"])

# creating a log file 
log_path = os.path.join(args["system_folder"], "log.txt")

# pass everything to a shell command
cmd = """java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path)
os.system(cmd)

read_evaluate_log(log_path)