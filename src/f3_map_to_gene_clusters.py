import os 
import json 

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

parser.add_argument('-i','--input_folder', help='The directory with reads in fastq.gz format.', required=True)
parser.add_argument('-db','--database', help='Path to KMA database from previous step.', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)
parser.add_argument('-s1','--suffix1', help='Suffix of the first of the paired reads', 
                    type=str, default="_paired_1.fastq.gz", required=False)
parser.add_argument('-s2','--suffix2', help='Suffix of the second of the paired reads', 
                    type=str, default="_paired_2.fastq.gz", required=False)
parser.add_argument('-t','--threads', help='Number of threads to use for clustering', 
                    type=int, default=1, required=False)


args = vars(parser.parse_args())
system_folder = os.path.join(args["output_folder"], "system")

script_dir = os.path.dirname(__file__)
config = read_json_config(os.path.join(script_dir, "config.json"))


output_path = args["output_folder"]
suffix1, suffix2 = args["suffix1"], args["suffix2"]

# load input template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "map_to_gene_clusters.json")
with open(template_path) as f:
    template = json.loads(f.read())

# collect files from dir
forward, reverse = [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(suffix1)], \
                   [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(suffix2)]

# modify template
for read_1, read_2 in zip(forward, reverse):
    template["map_to_gene_clusters.sampleInfo"].append({"file_r1": read_1, "file_r2": read_2, "sample_id": read_1.split(suffix1)[0]})

template["map_to_gene_clusters.thread_num"] = args["threads"]
template["map_to_gene_clusters.kma_db_file"] = args["database"]
template["map_to_gene_clusters.sample_suffix"] = suffix1

# creating output directory
create_directory(args["output_folder"])
create_directory(system_folder)

# writing input json
inputs_path = os.path.join(system_folder, 'input_map_to_gene_clusters.json')

with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)



paths = {
    "config_path" : config["db_mount_config"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"]["f3_map_to_gene_clusters"],
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