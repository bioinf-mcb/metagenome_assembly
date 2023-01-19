import os

from _utils import (
    modify_concurrency_config,
    get_files_with_extension,
    read_evaluate_log,
    check_inputs_not_empty,
    start_workflow,
    retrieve_config_paths,
    prepare_system_variables,
    write_inputs_file
)

import logging
logging.basicConfig(level=logging.DEBUG)

import argparse

## TODO test for single end reads

parser = argparse.ArgumentParser(description='Assemble quality controlled reads with MegaHIT.',
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

## TODO add all arguments from wdl script
parser.add_argument('-i','--input_folder', help='The directory with quality controlled reads', required=True)
parser.add_argument('-o','--output_folder', help='The directory for saving the output', required=True)

parser.add_argument('-min_len','--minimum_contig_length', help='Minimum length of the final contigs', default=500, type=int, required=False)
parser.add_argument('-s', "--suffix", help="Suffix to define input files", default=".anqdpht.fastq.gz", required=False)

parser.add_argument('-t','--threads', help='Number of threads to use', default=1, type=int, required=False)
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel',
                    type=int, default=1, required=False)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)

# getting sorted lists of forward and reverse reads from a folder
sequencing_files = get_files_with_extension(args["input_folder"], args["suffix"])

# counting samples
template["metagenome_assy.input_files"] = sequencing_files
template["metagenome_assy.threads"] = args["threads"]
template["metagenome_assy.min_contig_len"] = args["minimum_contig_length"]

# writing input json
inputs_path = write_inputs_file(template, system_folder, "_".join(["inputs", script_name]) + ".json")

# check inputs
check_inputs_not_empty({"reads" : template["metagenome_assy.input_files"]})

# creating absolute paths
paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

paths["db_mount_config"] = modify_concurrency_config(paths["db_mount_config"], system_folder, args["concurrent_jobs"])

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

# checking if the job was succesful
read_evaluate_log(log_path)