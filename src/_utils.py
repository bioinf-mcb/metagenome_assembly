import os
import re
import json
import configparser

import logging
logging.basicConfig(level=logging.DEBUG)


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
        config = config.replace("/storage/TomaszLab/vbez/metagenomic_gmhi/metagenomome_assembly/databases/GRCh38_bt2", 
                                f"{bt2_path}")
    out_config_path = os.path.join(output_path, "concurrency_config.conf") 
    with open(out_config_path, "w") as f:   
        f.write(config)
    return out_config_path
    
    
    