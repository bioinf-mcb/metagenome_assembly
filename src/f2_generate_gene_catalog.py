import os 
import json 

from _utils import (
    read_json_config,
    modify_output_config,
    modify_concurrency_config,
    create_directory,
    read_evaluate_log
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

# reading config file 
script_dir = os.path.dirname(__file__)
config = read_json_config(os.path.join(script_dir, "config.json"))

args = vars(parser.parse_args())

study_path = args["input_folder"]
system_folder = os.path.join(args["output_folder"], "system")

# load json template
script_dir = os.path.dirname(__file__)
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "generate_gene_catalogue.json")
with open(template_path) as f:
    template = json.loads(f.read())
    
# collect files from dir
files =  [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith(args["suffix"])]
template["generate_gene_catalog.genepreds"] = files
template["generate_gene_catalog.thread_num"] = args["threads"]

# creating output directory
create_directory(args["output_folder"])
create_directory(system_folder)

# writing input json
inputs_path = os.path.join(system_folder, 'input_gene_catalogue.json')
with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)


paths = {
    "config_path" : config["db_mount_config"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"]["f2_generate_gene_catalog"],
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
                                                 n_jobs=1)

# creating a log file 
log_path = os.path.join(system_folder, "log.txt")

# pass everything to a shell command
cmd = """java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path)
os.system(cmd)

read_evaluate_log(log_path)

# rename output folder
glob_name = [file for file in os.listdir(args["output_folder"]) if file.startswith("glob")][0]
os.rename(os.path.join(args["output_folder"], glob_name), os.path.join(args["output_folder"], "gene_catalog_split"))
    
