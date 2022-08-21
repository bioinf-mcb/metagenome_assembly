import os
import sys
import re
import json
import config 
import configparser

import logging
logging.basicConfig(level=logging.DEBUG)


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
    os.system(cmd)
    
    # Log download 
    logging.info(cmd)
    filename = url.split("/")[-1]
    logging.info(f"Downloaded {filename}")
    
    return filename 
    

def modify_config_file(filename: str, 
                       section: str, 
                       config_name: str,
                       config_value) -> None:

    config = configparser.ConfigParser()
    try: 
        config.read(filename)
    except FileNotFoundError:
        pass
    
    if not section in config.sections():
        config.add_section(section)
    
    config[section][config_name] = config_value
    with open(filename, "w") as configfile:
        config.write(configfile)
    logging.info(f"{filename} modified - {section}:{config_name} added")
    

def modify_output_config(path_to_file : str, 
                         output_path : str) -> None: 
    """Modifies Cromwell's output configuraton .json
    required for specification of the output directory"""
    
    # read initial file 
    with open(path_to_file, "r") as f: 
        output_params = json.loads(f.read())
        
    output_params["final_workflow_outputs_dir"] = output_path
    
    # save new config in the output path
    out_config_path = os.path.join(output_path, "output_config.json") 
    with open(out_config_path, "w") as f: 
        json.dump(output_params, f, indent=4, sort_keys=True, ensure_ascii=False)
    
    return out_config_path

def modify_concurrency_config(path_to_file : str, 
                              output_path : str, 
                              n_jobs: int, 
                              bt2_path: str=None) -> None: 
    """Modifies Cromwell's config configuraton .json
    required running multiple jobs in parallel"""
    
    # read initial file 
    with open(path_to_file, "r") as f: 
        config = f.read()
        
    config = config.replace("concurrent-job-limit = 8", f"concurrent-job-limit = {n_jobs}")
    if bt2_path is not None: 
        config = config.replace("bt2_index_path", 
                                f"{bt2_path}")
    out_config_path = os.path.join(output_path, "concurrency_config.conf") 
    with open(out_config_path, "w") as f:   
        f.write(config)
        
    return out_config_path


def unpack_archive(zip_path, unpack_folder):
    unpack_path = os.path.abspath(unpack_folder)
    os.system(f"unzip {zip_path} -d {unpack_folder}")
    os.remove(zip_path)
    
    return unpack_path
    

def find_database_index(directory, all_extensions):
    """
    Search through the directory for Bowtie2 index files
    """
    
    index=""
        
    # sort the extensions with the longest first, to test the most specific first
    # to find the index
    all_extensions.sort(key=lambda x: len(x), reverse=True)
    
    if not os.path.isdir(directory):
        # check if this is the database index file
        if os.path.isfile(directory):
            # check for the database extension
            for extension in all_extensions:
                if re.search(extension+"$",directory):
                    index=directory.replace(extension,"")
                    break
        else:
            # check if this is the basename of the index files
            # only need to check the first three (to include bowtie2 large index)
            for extension in all_extensions[:3]:
                if os.path.isfile(directory+extension):
                    index=directory
                    break
    else:
        # search through the files to find one with the bowtie2 extension
        for file in os.listdir(directory):
            # look for an extension for a standard and large bowtie2 indexed database
            for extension in all_extensions:
                if re.search(extension+"$",file):
                    index=os.path.join(directory,file.replace(extension,""))
                    break
            if index:
                break
    
    if not index:
        logging.info(f"Unable to find Bowtie2 index files in directory: {directory}\n")
    
    return index
    
    
    