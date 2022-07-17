import os
import re

from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup, SoupStrainer

import argparse

from _utils import (
    aria2c_download_file,
    modify_config_file
)

from typing import List

import logging
logging.basicConfig(level=logging.INFO)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)


def find_link(url: str) -> str:
    '''
    Grabs the link to the latest Cromwell release.
    Parameters:
    __________
    url : str
        Url with the latest Cromwell workflow manager version.
    Returns:
    ________
    str 
        The exact link to Cromwell latest release.
    '''
    
    # grab hyperlink from latest release url    
    base = "https://github.com/"
    response = requests.get(url)

    for link in BeautifulSoup(response.content, parse_only=SoupStrainer('a'), features="html.parser"):
        if link.has_attr('href') and link['href'].endswith(".jar") and "cromwell" in link['href']:
            return urljoin(base, link['href'])

def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'([0-9]+)', text)]


def retrieve_cromwell_version(folder: str) -> List[str]:
    """
    Returns the version of cromwell installed in the folder.
    """
    versions = [filename for filename in os.listdir(folder) if "cromwell" in filename]
    versions.sort(key=natural_keys, reverse=True)
    return [os.path.join(folder, version) for version in versions]

def delete_older_releases(old_cromwell_versions: List[str]):

    string_older_releases = ", ".join(old_cromwell_versions)
    logging.info(f"Older releases {string_older_releases} removed")
    for item in old_cromwell_versions:
        os.remove(item)

def download_cromwell(link: str, cromwell_dir: str) -> str:
    """
    Downloads Cromwell from link
    """
    filename = aria2c_download_file(link, cromwell_dir)
    cromwell_path = os.path.abspath(os.path.join(cromwell_dir, filename))
    return cromwell_path




def setup_cromwell(url, save_dir):
    
    link = find_link(url)
    latest_version_online = link.split("/")[-1]
    os.makedirs(save_dir, exist_ok=True)
    cromwell_dir = os.path.join(save_dir, "cromwell")
    
    if os.path.isdir(cromwell_dir):
        versions = retrieve_cromwell_version(cromwell_dir)
        
        # check if any cromwell file was found
        if versions:
            latest_version_local = versions[0].split("/")[-1] 
            if latest_version_local == latest_version_online:
                cromwell_path = os.path.join(cromwell_dir, latest_version_local)
                return cromwell_path
        else:
            cromwell_path = download_cromwell(link, cromwell_dir)
            delete_older_releases(versions)

            return cromwell_path
    else:
        os.makedirs(cromwell_dir)
        cromwell_path = download_cromwell(link, cromwell_dir)
        
        return cromwell_path
    

    
    
    
if __name__ == "__main__":
    url = "https://github.com/broadinstitute/cromwell/releases/latest"

    parser = argparse.ArgumentParser()
    parser.add_argument("--save_dir", 
                        help='Directory to use for Cromwell download.', required=True)
    parser.add_argument("--config_file",
                        help='Path for saving the config file.', 
                        type=str, default="./")    

    args = vars(parser.parse_args())
    cromwell_path = setup_cromwell(url, args["save_dir"])
    latest_version = cromwell_path.split('/')[-1].split('.')[0]
    logging.info(f"The latest release {latest_version} was installed")

    modify_config_file(os.path.join(args["config_file"], "config.ini"), 
                       "cromwell", 
                       "cromwell_path", 
                       os.path.abspath(cromwell_path))

    
    