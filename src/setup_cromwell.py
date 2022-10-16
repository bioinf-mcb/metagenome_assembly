import os
import re

from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup, SoupStrainer

import argparse

from _utils import (
    aria2c_download_file,
    modify_json_config
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

    for element in BeautifulSoup(response.content, parse_only=SoupStrainer('a'), features="html.parser"):
        if element.has_attr('href') and "releases/tag" in element['href']:
            expanded_assets_url = re.sub("tag", "expanded_assets", element["href"])
    
    response = requests.get(urljoin(base, expanded_assets_url))
    for element in BeautifulSoup(response.content, parse_only=SoupStrainer('a'), features="html.parser"):
        if element.has_attr('href') and "cromwell" in element['href'] and element["href"].endswith(".jar"):
            link = urljoin(base, element["href"])
        
        return link

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

    if old_cromwell_versions:
        for version in old_cromwell_versions:
            os.remove(version)
        string_older_releases = ", ".join(old_cromwell_versions)
        logging.info(f"Older releases {string_older_releases} removed")

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
    
    if os.path.isdir(save_dir):
        
        versions = retrieve_cromwell_version(save_dir)
        # check if any cromwell file was found
        if versions:
            latest_version_local = versions[0].split("/")[-1]
            # check if the latest version is already installed
            if latest_version_local == latest_version_online:
                cromwell_path = os.path.join(save_dir, versions[0])
        # if no cromwell file was found, download the latest version
        # also downloads latest version if the latest version is not installed
        else:    
            cromwell_path = download_cromwell(link, save_dir)
            delete_older_releases(versions[1:])

    else:
        os.makedirs(save_dir)
        cromwell_path = download_cromwell(link, save_dir)

    return cromwell_path

from time import sleep
    
if __name__ == "__main__":
    url = "https://github.com/broadinstitute/cromwell/releases/latest"

    parser = argparse.ArgumentParser()
    parser.add_argument("--save_path", 
                        help='Path to save Cromwell.', required=True) 

    args = vars(parser.parse_args())
    cromwell_path = os.path.abspath(setup_cromwell(url, args["save_path"]))
    script_dir = os.path.dirname(__file__)

    modify_json_config(os.path.join(script_dir, "config.json"), "cromwell_path", cromwell_path)

    
    