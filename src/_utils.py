import os
import sys
import re
import json
import glob
from typing import Dict, List

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme

console = Console()

import logging
logging.basicConfig(level=logging.DEBUG)


def get_files_with_extension(directory, extension):
    """
    Get all files with a specific extension in a directory.
    """
    return glob.glob(f"{directory}/**/*{extension}", recursive=True)

def reorder_list_substrings(list_of_strings, substrings):
    """
    Reorder a list of strings based on the order of substrings.
    """
    return [list_item for substring in substrings for list_item in list_of_strings if substring in list_item]



def check_path_dir(*paths):
    for path in paths:
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise OSError(2, "Path is not a directory. Please provide a path to a folder.")


def create_directory(directory):
    """ Try to create a directory if it does not exist """
    message = f"Creating output directory: {directory}"
    logging.debug(message)
    try:
        os.makedirs(directory, exist_ok=True)
    except EnvironmentError:
        message = f"Unable to create output directory: {directory}"
        logging.critical(message)
        sys.exit(message)


def aria2c_download_file(url: str, save_dir: str) -> str:
    '''
    Downloads object from url using aria2c.

    Parameters:
    ___________

    url : str
        Url to download the file from.
    save_dir : str
        Filepath to a folde to save file in.

    Returns:
    ________
    filename : str
        Name of the downloaded file.
    '''

    cmd = (
    f'aria2c -x 16 -j 16 -c {url} -d {save_dir}'
    )

    logging.info(cmd)
    os.system(cmd)

    # Log download
    filename = url.split("/")[-1]
    logging.info(f"Downloaded {filename}")

    return filename

def modify_json_config(config_file: str,
                       config_name: str,
                       config_value: str,
                       subsection: str=None) -> None:
    """Modifies a json config file"""
    with open(config_file, "r") as f:
        config = json.loads(f.read())
    if subsection:
        config[subsection][config_name] = config_value
        logging.debug(f"{config_file} modified - {subsection}:{config_name}:{config_value}")
    else:
        config[config_name] = config_value
        logging.debug(f"{config_file} modified - {config_name}:{config_value}")

    with open(config_file, "w") as f:
        json.dump(config, f, indent=4, sort_keys=True, ensure_ascii=False)



def read_json_config(config_file: str) -> dict:
    """Reads a json config file and returns a dictionary"""
    with open(config_file, "r") as f:
        config = json.loads(f.read())
    return config


def modify_output_config(path_to_file : str,
                         output_path : str,
                         save_path : str) -> str:
    """Modifies Cromwell's output configuraton .json
    required for specification of the output directory"""

    # read initial file
    with open(path_to_file, "r") as f:
        output_params = json.loads(f.read())

    output_params["final_workflow_outputs_dir"] = output_path

    # save new config in the output path
    out_config_path = os.path.join(save_path, "output_config.json")
    with open(out_config_path, "w") as f:
        json.dump(output_params, f, indent=4, sort_keys=True, ensure_ascii=False)

    return out_config_path

def modify_concurrency_config(path_to_file : str,
                              output_path : str,
                              n_jobs: int,
                              rcq_path: str=None,
                              gtdbtk_path: str=None,
                              eggnog_path: str=None) -> str:
    """Modifies Cromwell's config mount.json required for mounting databases from filesystem
    and running multiple jobs in parallel"""

    # read initial file
    with open(path_to_file, "r") as f:
        config = f.read()

    config = config.replace("concurrent-job-limit = 8", f"concurrent-job-limit = {n_jobs}")

    if rcq_path is not None:
        config = config.replace("rcq_database_path",
                                f"{rcq_path}")
    elif gtdbtk_path is not None:
        config = config.replace("gtdbtk_data_path",
                                f"{gtdbtk_path}")
    elif eggnog_path is not None:
        config = config.replace("eggnog_data_path",
                                f"{eggnog_path}")

    out_config_path = os.path.join(output_path, "mount.conf")
    with open(out_config_path, "w") as f:
        f.write(config)

    return out_config_path


def unpack_archive(archive_path, unpack_folder, remove_archive=True):
    unpack_path = os.path.abspath(unpack_folder)

    if archive_path.endswith(".zip"):
        cmd = f"unzip -q {archive_path} -d {unpack_path}"
    elif archive_path.endswith("tar.gz"):
        cmd = f"tar -xzf {archive_path} -C {unpack_path}"
    elif archive_path.endswith(".gz"):
        filename = ".".join(archive_path.split("/")[-1].split('.')[:-1])
        cmd = f"gunzip -c {archive_path} > {os.path.join(unpack_path, filename)}"
    else:
        raise ValueError("Archive format is not supported.")

    logging.info(f"Unpacking {archive_path} to {unpack_path}")
    os.system(cmd)

    if remove_archive:
        os.remove(archive_path)

    return unpack_path


def find_database(database_path, all_extensions, database_name):
    """
    Search through the directory for database files.
    """

    index=""

    # sort the extensions with the longest first, to test the most specific first
    # to find the index
    all_extensions.sort(key=lambda x: len(x), reverse=True)
    if os.path.isfile(database_path):
        for extension in all_extensions:
            if re.search(extension+"$", database_path):
                index=database_path.replace(extension,"")
                logging.info(f"Treating {index} as {database_name}.")
                return index

    for fname in glob.glob(database_path+"/**/*", recursive=True):
        for extension in all_extensions:
            if re.search(extension+"$",fname):
                index = os.path.abspath(os.path.dirname(fname))
                logging.info(f"Treating {index} as directory with {database_name}.")
                return index

    if not index:
        logging.info(f"Unable to find {database_name} files in directory: {database_path}.")

    return index

def download_database(save_dir, url, database_name, database_description):
    """
    Download a database from a url to a save directory.
    """

    message = f"{database_name} database will be downloaded. {database_description}"
    logging.info(message)
    zip_filename = aria2c_download_file(url, save_dir)
    zip_filepath = os.path.join(save_dir, zip_filename)
    database_path = unpack_archive(zip_filepath, save_dir)
    return database_path

def check_or_download_database(database_path, extensions, software_name, database_name, database_url, database_description):
    """
    Check if the database is present in the database_path. If not, download it.
    """
    db = find_database(database_path, extensions, software_name)
    if not db:
        db_folder = download_database(database_url, database_path, database_name, database_description)
        db = find_database(db_folder, extensions, software_name)

    return database_path

def infer_split_character(base_name):
    "Infer if fastq filename uses '_R1' '_1' to seperate filenames"

    # infer split character if necessary only the first time.

    if ("_R1" in base_name) or ("_R2" in base_name):
        split_character = "_R"

    elif ("_1" in base_name) or ("_2" in base_name):
        split_character = "_"

    else:
        raise ValueError("Unable to infer split character from filename. Please specify it manually.")

    if split_character is not None:

        logging.info(
            f"I inferred that {split_character}1 and {split_character}2 distinguish paired end reads."
        )

    return split_character


def filter_list_of_terms(key_terms, list_of_terms):
    """
    Filter a list of terms based on a list of key terms.
    """
    return [term for term in list_of_terms if any(key_term in term for key_term in key_terms)]


def read_evaluate_log(log_path):
    """ Reads the Cromwell log and checks wherher the workflow was successful or not"""
    with open(log_path, "r") as f:
        log = f.read()
    if "workflow finished with status 'Succeeded'" in log:
        console.log("Workflow finished successfully.", style="green")
    else:
        console.log("Workflow failed. Check the log file.", style="red")


def check_inputs_not_empty(inputs: Dict[str, List]) -> None:
    """Checks if all lists are not empty"""
    for name, input_ in inputs.items():
        if len(input_) == 0:
            console.log(f"Workflow failed. Input {name} is empty. Check the inputs in the system files.", style="red")
            sys.exit(1)

def start_workflow(system_paths, inputs_path, system_folder, workflow_name, console=console):
    """Starts the workflow. Redirects output to a log file and returns the log path for evaluation"""
    console.log(f"Workflow [bold yellow]{workflow_name}[/bold yellow] has started. Please, be patient.")

    with console.status("[yellow]Processing data..."):
        log_path = os.path.join(system_folder, "log.txt")
        if workflow_name == "qc":
            cmd = """java -Dconfig.file={1} -jar {0} run {2} -i {3} > {4}""".format(*system_paths.values(), inputs_path, log_path)
        else:
            cmd = """java -Dconfig.file={1} -jar {0} run {3} -o {2} -i {4} > {5}""".format(*system_paths.values(), inputs_path, log_path)
        os.system(cmd)

    return log_path

def load_input_template(script_dir, script_name, config):
    template_path = os.path.abspath(os.path.join(script_dir, config["input_templates"][script_name]))
    with open(template_path) as f:
        template = json.loads(f.read())

    return template


def retrieve_config_paths(config, script_dir, script_name, **kwargs):
    """Returns paths to the config files"""

    paths = config["system_paths"]
    paths["wdl_path"] = config["wdls"][script_name]

    for entry, path in paths.items():
        paths[entry] = os.path.abspath(os.path.join(script_dir, path))

    # paths["output_config_path"] = modify_output_config(paths["output_config_path"], **kwargs)

    return paths

def prepare_system_variables(argparser, py_script):
    """Loads system variables for the script"""
    # Getting necessary files from script name
    script_name = os.path.basename(py_script).split(".")[0]
    # reading config file
    script_dir = os.path.dirname(py_script)
    config = read_json_config(os.path.join(script_dir, "config.json"))
    # parsing arguments
    args = vars(argparser.parse_args())
    system_folder = os.path.join(args["output_folder"], "system")
    if script_name not in ["t1_predict_mags", "generate_table"]:
        args["input_folder"] = os.path.abspath(args["input_folder"])
        check_path_dir(args["input_folder"])

    # creating output directory
    create_directory(args["output_folder"])
    create_directory(system_folder)

    # checking if input directory exists

    # load input template
    template = load_input_template(script_dir, script_name, config)

    return script_name, script_dir, config, args, system_folder, template

def write_inputs_file(inputs_template, system_folder, inputs_filename):
    """Writes the inputs to a system folder for troubleshooting and returns the path to the file"""
    inputs_path = os.path.join(system_folder, inputs_filename)
    with open(inputs_path, 'w') as f:
        json.dump(inputs_template, f, indent=4, sort_keys=True, ensure_ascii=False)
    return inputs_path