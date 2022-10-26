from distutils.command.config import config
import os 
import json
import sys 

from _utils import (
    check_inputs_not_empty,
    read_evaluate_log,
    start_workflow,
    prepare_system_variables,
    write_inputs_file,
    retrieve_config_paths
)

import argparse

# Command line argyments
parser = argparse.ArgumentParser(description='Generate read count table post KneadData QC')
parser.add_argument('-i','--input_folder', help='The directory with KneadData logs', required=True)
parser.add_argument('-o','--output_folder', help='The directory for the output', required=True)

script_name, script_dir, config, args, system_folder, template = prepare_system_variables(parser, __file__)

logs  = [os.path.join(args["input_folder"], file) for file in sorted(os.listdir(args["input_folder"])) if file.endswith(".log")]
    
# json template
read_table_input = {"read_table.logs" : logs}

inputs_path = write_inputs_file(read_table_input, system_folder, "_".join(["inputs", script_name]) + ".json")

# check inputs
check_inputs_not_empty({"logs" : logs})

paths = retrieve_config_paths(config, script_dir, script_name, output_path=args["output_folder"], save_path=system_folder)

# starting workflow
log_path = start_workflow(paths, inputs_path, system_folder, script_name)

read_evaluate_log(log_path)