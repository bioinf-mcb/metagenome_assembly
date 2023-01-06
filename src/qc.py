import os
import re

from _utils import (
    modify_concurrency_config,
    infer_split_character,
    filter_list_of_terms,
    read_evaluate_log,
    find_database,
    download_database,
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

parser = argparse.ArgumentParser(description='Quality control and assembly of contigs for paired metagenomic reads.'
                                            'The succesful execution of this step requires RCQFilterData Database',
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

## TODO add all arguments from wdl script
parser.add_argument('-i','--input_folder', help='The directory with raw reads in .fastq or fastq.gz\
                    format', required=True)

parser.add_argument('-t','--threads', help='Number of threads to use', default=1, type=int, required=False)
parser.add_argument('-o','--output_folder', help='The directory for saving the output', required=True)
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel',
                    type=int, default=1, required=False)
parser.add_argument('-db_path','--database_path', help= 'Path to a diretory with RCQFilterData Database If directory does not contain'
                                                        'required index GRCh38 database would be downloaded for'
                                                        'decontamination of samples from human DNA.', required=True)
parser.add_argument('-split_char','--split_character', help='Character used to separate paired reads. Software can deduct use of "_" and "_R", otherwise it will fail. \
                    Ex. SAMPLE_1(R).fastq  SAMPLE_2(R).fastq. If you have reads with different naming convention, please specify it here.', required=False)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)

database_path = find_database(args["database_path"].split("/")[0], ["refdata"], "RCQFilterData Database")

if not database_path:
    description = "It will allow to remove contaminant DNA from samples."
    database_folder = download_database(args["database_path"], config["rcqfilter_url"],
                                       "RQCFilterData Database", description)
    database_path  = find_database(database_folder, [args["database_path"]], "RCQFilterData Database'")

# getting sorted lists of forward and reverse reads from a folder
sequencing_files = filter_list_of_terms(config["read_extensions"], os.listdir(args["input_folder"]))
split_character = infer_split_character(sequencing_files[0])
base_names = [f"{split_character}".join(id.split(split_character)[:-1]) for id in sequencing_files]

# find all read files in a folder and prepare them for processing
for base in set(base_names):
    r1 = [id for id in sequencing_files if re.search(base+split_character+"1", id)]
    r2 = [id for id in sequencing_files if re.search(base+split_character+"2", id)]
    r1_full_path = os.path.join(args["input_folder"], r1[0])
    r2_full_path = os.path.join(args["input_folder"], r2[0])
    template["jgi_rqcfilter.input_fq1"].append(r1_full_path)
    template["jgi_rqcfilter.input_fq2"].append(r2_full_path)

# counting samples
n_samples = len(template["jgi_rqcfilter.input_fq1"])
logging.info(f"Found samples: {n_samples}")

# changing number of threads
template['jgi_rqcfilter.threads'] = args["threads"]

# passing the database
template["jgi_rqcfilter.database"] =  os.path.abspath(args["database_path"])
# passing output dir
template["jgi_rqcfilter.outdir"] = os.path.abspath(args["output_folder"])

# writing input json
inputs_path = write_inputs_file(template, system_folder, "_".join(["inputs", script_name]) + ".json")

# check inputs
check_inputs_not_empty({"reads" : template["jgi_rqcfilter.input_fq1"]})

paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

paths["db_mount_config"] = modify_concurrency_config(paths["db_mount_config"], system_folder, args["concurrent_jobs"])

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

# checking if the job was succesful
read_evaluate_log(log_path)