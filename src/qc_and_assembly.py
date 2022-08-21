import os 
import json 
import re
import config 

from rich.console import Console
console = Console()

from _utils import (
    check_path_dir,
    modify_output_config,
    modify_concurrency_config,
    aria2c_download_file,
    unpack_archive,
    create_directory,
    find_database_index
)

import logging
logging.basicConfig(level=logging.DEBUG)

import argparse

## TODO test for single end reads
parser = argparse.ArgumentParser(description='Quality control and assembly of contigs for paired metagenomic reads.'
                                             'The succesful execution of this step requires Bowtie2 index.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

## TODO add all arguments from wdl script
parser.add_argument('-i','--input_folder', help='The directory with raw reads in .fastq or fastq.gz\
                    format', required=True)
parser.add_argument('-t','--threads', help='Number of threads to use', default=1, type=int, required=False)
parser.add_argument('-o','--output_dir', help='The directory for the output', required=True)
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel', 
                    type=int, default=1, required=False)
parser.add_argument('-bt2_index','--bowtie2_index', help='Path to a diretory with Bowtie2 index. If directory does not contain' 
                                                         'required index GRCh38 database would be downloaded for' 
                                                         'decontamination of samples from human DNA.', required=True)

args = vars(parser.parse_args())

# check if provided path is a dir 


study_path = os.path.abspath(args["input_folder"])
threads = args["threads"]
output_path = args["output_dir"]
system_path = os.path.join(output_path, "system")
bowtie2_folder = args["bowtie2_index"]
check_path_dir(study_path)
index = find_database_index(bowtie2_folder, config.bowtie2_index_formats)

if not index:
    zip_filename = aria2c_download_file(config.grch38_url, bowtie2_folder)
    zip_filepath = os.path.join(bowtie2_folder, zip_filename)
    bowtie2_folder = unpack_archive(zip_filepath, bowtie2_folder)
    message = "GRCh38 database will be downloaded.  It will allow to remove human contaminant DNA from samples."
              "Downloading GRCh38..."
    logging.info(message)

# getting sorted lists of forward and reverse reads from a folder
forward, reverse = [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_1.fastq.gz")], \
                   [os.path.join(study_path, file) for file in sorted(os.listdir(study_path)) if file.endswith("_2.fastq.gz")]

script_dir = os.path.dirname(__file__)

## TODO modify template to include all arguments
# template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "qc_and_assemble.json")
with open(template_path) as f:
    template = json.loads(f.read())

# adding files to json
for r1, r2 in zip(forward, reverse):
    template["qc_and_assemble.sampleInfo"].append({"file_r1": r1, "file_r2": r2})

    # adding threads
template['qc_and_assemble.thread_num'] = threads
    
print("Found samples:")
print(len(template["qc_and_assemble.sampleInfo"]))    

# creating output directory
create_directory(output_path, exist_ok=True)
create_directory(system_path, exist_ok=True)

# writing input json
inputs_path = os.path.join(system_path, 'inputs.json')
with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)

    
script_dir = os.path.dirname(__file__)

log_path = os.path.join(system_path, "log.txt")

paths = {
    "config_path" : config.kneaddata_config, 
    "cromwell_path" : config.cromwell_dir, 
    "wdl_path" : config.wdl_paths["qc_and_assemble"],
    "output_config_path" : config.output_config
}

for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))

paths["output_path"] = modify_output_config(paths["output_path"], output_path)
paths["config_path"] = modify_concurrency_config(paths["config_path"], system_path, 
                                                args["concurrent_jobs"], os.path.abspath(bowtie2_folder))

os.system("""java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} >> {5}""".format(*paths.values(), inputs_path, log_path))

with open(log_path) as f:
    log = f.read()

if "workflow finished with status 'Succeeded'" in log:
    console.log("Workflow finished successfully", style="green")
else:
    console.log("Workflow failed, check the log file", style="red")