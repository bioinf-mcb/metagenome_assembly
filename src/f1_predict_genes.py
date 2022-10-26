from _utils import (
    modify_concurrency_config, 
    read_evaluate_log,
    get_files_with_extension,
    check_inputs_not_empty,
    start_workflow,
    write_inputs_file,
    retrieve_config_paths,
    prepare_system_variables
)

import argparse
# Command line argyments
parser = argparse.ArgumentParser(description='Predict genes using Prodigal', 
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--input_folder', help='The directory with contigs in .fa format', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)
parser.add_argument('-s','--suffix', help='Suffix of the filename to be identified in input folder & replaced in the output(i.e. -s .fa  -i ID7.fa -> ID7.fna)', 
                    type=str, default=".min500.contigs.fa")
parser.add_argument('-c','--concurrent_jobs', help='Number of jobs to run in parallel', 
                    type=int, default=1, required=False)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)
    
# collect contigs from dir
contigs =  get_files_with_extension(args["input_folder"], args["suffix"])
template["predict_mags.contigs"] = contigs
template["predict_mags.sample_suffix"] = args["suffix"]

# writing input json
inputs_path = write_inputs_file(template, system_folder, "_".join(["inputs", script_name]) + ".json")

# checking input 
check_inputs_not_empty({"contigs" : contigs})

paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

# modifying config to change number of concurrent jobs and mount dbs
paths["db_mount_config"] = modify_concurrency_config(paths["db_mount_config"], 
                                                     system_folder, 
                                                     args["concurrent_jobs"])

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

# checking if the job was successful
read_evaluate_log(log_path)