import os 
import json 
import sys
from _utils import (
    modify_output_config,
    modify_concurrency_config
)

import argparse

# Command line argyments
parser = argparse.ArgumentParser(description='Predict genes using Prodigal', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--input', help='The directory with contigs in .fa format', required=True)
parser.add_argument('-o','--output_dir', help='The directory for the output', required=True)
parser.add_argument('-s','--suffix', help='Suffix of the filename to be identified in input folder & replaced in the output(i.e. -s .fa  -i ID7.fa -> ID7.fna)', 
                    type=str, default=".min500.contigs.fa")
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel', 
                    type=int, default=1, required=False)


args = vars(parser.parse_args())

study_path = args["input"]
output_path = args["output_dir"]
filename_suffix = args["suffix"]
n_jobs = args["concurrent_jobs"]

# load json template
script_dir = os.path.dirname(__file__)

# template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "predict_genes.json")
with open(template_path) as f:
    template = json.loads(f.read())
    
# collect files from dir
files =  [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith(filename_suffix)]
template["predict_mags.contigs"] = files
template["predict_mags.sample_suffix"] = filename_suffix

# writing input json
os.makedirs(output_path, exist_ok=True)
inputs_path = os.path.join(output_path, 'input_predict_genes.json')

with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)

    
script_dir = os.path.dirname(__file__)

paths = {
    "config_dir" : "./cromwell_configs/kneaddata.conf", 
    "cromwell_dir" : "../cromwell/cromwell-80.jar", 
    "wdl_dir" : "./wdl/f1_predict_genes.wdl",
    "output_dir" : "json_templates/output_options.json"
}

# creating absolute paths
for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

paths["output_dir"] = modify_output_config(paths["output_dir"], output_path)
paths["config_dir"] = modify_concurrency_config(paths["config_dir"], output_path, n_jobs)

log_path = os.path.join(output_path, "log.txt")
# pass everything to a shell command
os.system("""java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path))