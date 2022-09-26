import os 
import json 
import sys
from _utils import (
    modify_output_config,
    modify_concurrency_config,
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

reads_path = args["input_folder"]
output_path = args["output_folder"]
suffix1, suffix2 = args["suffix1"], args["suffix2"]

# load json template
script_dir = os.path.dirname(__file__)

# collect files from dir
forward, reverse = [os.path.join(reads_path, file) for file in sorted(os.listdir(reads_path)) if file.endswith(suffix1)], \
                   [os.path.join(reads_path, file) for file in sorted(os.listdir(reads_path)) if file.endswith(suffix2)]

# load template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "map_to_gene_clusters.json")
with open(template_path) as f:
    template = json.loads(f.read())

# modify template
for read_1, read_2 in zip(forward, reverse):
    template["map_to_gene_clusters.sampleInfo"].append({"file_r1": read_1, "file_r2": read_2})

template["map_to_gene_clusters.thread_num"] = args["threads"]
template["map_to_gene_clusters.kma_db_file"] = args["database"]
template["map_to_gene_clusters.sample_suffix"] = suffix1

# writing input json
create_directory(args["output_folder"])
inputs_path = os.path.join(output_path, 'input_map_to_gene_clusters.json')

with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)

    
script_dir = os.path.dirname(__file__)

paths = {
    "config_path" : config["db_mount_config"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"]["f3_map_to_gene_clusters"],
    "output_config_path" : config["output_config_path"]
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

paths["output_dir"] = modify_output_config(paths["output_dir"], output_path)

log_path = os.path.join(output_path, "log.txt")
# pass everything to a shell command
os.system("""java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path))

read_evaluate_log(log_path)