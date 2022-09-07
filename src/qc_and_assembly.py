import os 
import json 
import re

from rich.console import Console
console = Console()

from _utils import (
    read_json_config,
    check_path_dir,
    modify_output_config,
    modify_concurrency_config,
    aria2c_download_file,
    unpack_archive,
    create_directory,
    find_database_index,
    infer_split_character, 
    filter_list_of_terms
)

import logging
logging.basicConfig(level=logging.DEBUG)

import argparse

## TODO test for single end reads
# check if provided path is a dir 

def parse_args(args):
    args["study_path"] = os.path.abspath(args["input_folder"])
    args["system_path"] = os.path.join(args["output_folder"], "system")
    return args

def download_grch(url, destination):
    logging.info("GRCh38 database will be downloaded.  It will allow to remove human contaminant DNA from samples.")
    zip_filename = aria2c_download_file(url, destination)
    zip_filepath = os.path.join(destination, zip_filename)
    bowtie2_folder = unpack_archive(zip_filepath, destination)
    message = "Downloaded GRCh38."
    logging.info(message)
    return bowtie2_folder

parser = argparse.ArgumentParser(description='Quality control and assembly of contigs for paired metagenomic reads.'
                                            'The succesful execution of this step requires Bowtie2 index.',
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

## TODO add all arguments from wdl script
parser.add_argument('-i','--input_folder', help='The directory with raw reads in .fastq or fastq.gz\
                    format', required=True)

parser.add_argument('-t','--threads', help='Number of threads to use', default=1, type=int, required=False)
parser.add_argument('-o','--output_folder', help='The directory for saving the output', required=True)
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel', 
                    type=int, default=1, required=False)
parser.add_argument('-bt2_index','--bowtie2_index', help='Path to a diretory with Bowtie2 index. If directory does not contain' 
                                                        'required index GRCh38 database would be downloaded for' 
                                                        'decontamination of samples from human DNA.', required=True)

args = vars(parser.parse_args())

script_dir = os.path.dirname(__file__)
config = read_json_config(os.path.join(script_dir, "config.json"))

args = parse_args(args)
check_path_dir(args["study_path"])

bowtie2_folder = find_database_index(args["bowtie2_index"], config["bowtie2_index_formats"])
if not bowtie2_folder:
    bowtie2_folder = download_grch(config["grch38_url"], args["bowtie2_index"])
    bowtie2_folder = find_database_index(bowtie2_folder, config["bowtie2_index_formats"])

# getting sorted lists of forward and reverse reads from a folder
sequencing_files = filter_list_of_terms(config["read_extensions"], os.listdir(args["study_path"]))
split_character = infer_split_character(sequencing_files[0])
base_names = [id.split(split_character)[0] for id in sequencing_files]

## TODO modify template to include all arguments
# template
template_dir = os.path.abspath(os.path.join(script_dir, "json_templates"))
template_path = os.path.join(template_dir, "qc_and_assemble.json")
with open(template_path) as f:
    template = json.loads(f.read())

for base in set(base_names):
    r1 = [id for id in sequencing_files if re.search(base+split_character+"1", id)]
    r2 = [id for id in sequencing_files if re.search(base+split_character+"2", id)]
    r1_full_path = os.path.join(args["study_path"], r1[0])
    r2_full_path = os.path.join(args["study_path"], r2[0])
    template["qc_and_assemble.sampleInfo"].append({"sample_id" : base, 
                                                   "file_r1": r1_full_path, 
                                                   "file_r2": r2_full_path})

# counting samples   
n_samples = len(template["qc_and_assemble.sampleInfo"]) 
logging.info(f"Found samples: {n_samples}")

# changing number of threads
template['qc_and_assemble.thread_num'] = args["threads"]

# creating output directory
create_directory(args["output_folder"])
create_directory(args["system_path"])

# writing input json
inputs_path = os.path.join(args["system_path"], 'inputs.json')
with open(inputs_path, 'w') as f:
    json.dump(template, f, indent=4, sort_keys=True, ensure_ascii=False)

log_path = os.path.join(args["system_path"], "log.txt")

paths = {
    "config_path" : config["configs"]["kneaddata"], 
    "cromwell_path" : config["cromwell_path"], 
    "wdl_path" : config["wdls"]["qc_and_assemble"],
    "output_config_path" : config["output_config_path"]
}

for path in paths.keys():
    paths[path] = os.path.abspath(os.path.join(script_dir, paths[path]))


paths["output_config_path"] = modify_output_config(paths["output_config_path"], args["output_folder"])
paths["config_path"] = modify_concurrency_config(paths["config_path"], args["system_path"], 
                                                args["concurrent_jobs"], os.path.abspath(bowtie2_folder))

cmd = """java -Dconfig.file={0} -jar {1} run {2} -o {3} -i {4} > {5}""".format(*paths.values(), inputs_path, log_path)
os.system(cmd)

with open(log_path) as f:
    log = f.read()

if "workflow finished with status 'Succeeded'" in log:
    console.log("Workflow finished successfully", style="green")
else:
    console.log("Workflow failed, check the log file", style="red")



