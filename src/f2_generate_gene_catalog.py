import os 
import json 
import sys
from _utils import (
    modify_output_config,
    modify_concurrency_config
)

import argparse

# Command line argyments
parser = argparse.ArgumentParser(description='Cluster genes predicted by Prodigal into gene catalog.', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--input', help='The directory with predicted genes in .fna format', required=True)
parser.add_argument('-o','--output_dir', help='The directory for the output', required=True)
parser.add_argument('-s','--suffix', help='Suffix of the filename to be identified in input folder & replaced in the output(i.e. -s .fa  -i ID7.fa -> ID7.fna)', 
                    type=str, default=".fna")
parser.add_argument('-t','--threads', help='Number of threads to use for clustering', 
                    type=int, default=1, required=False)


args = vars(parser.parse_args())

study_path = args["input"]
output_path = args["output_dir"]
filename_suffix = args["suffix"]

# load json template
script_dir = os.path.dirname(__file__)

# template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "gene_catalogue.json")
with open(template_path) as f:
    template = json.loads(f.read())
    
# collect files from dir
files =  [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith(filename_suffix)]
template["generate_gene_catalog.genepreds"] = files
template["generate_gene_catalog.thread_num"] = args["threads"]

# writing input json
os.makedirs(output_path, exist_ok=True)
inputs_path = os.path.join(output_path, 'input_gene_catalogue.json')

with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)

    
script_dir = os.path.dirname(__file__)

paths = {
    "config_dir" : "./cromwell_configs/kneaddata.conf", 
    "cromwell_dir" : "../cromwell/cromwell-80.jar", 
    "wdl_dir" : "./wdl/f2_generate_gene_catalog.wdl",
    "output_dir" : "json_templates/output_options.json"
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

paths["output_dir"] = modify_output_config(paths["output_dir"], output_path)

log_path = os.path.join(output_path, "log.txt")
# pass everything to a shell command
os.system("""java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path))