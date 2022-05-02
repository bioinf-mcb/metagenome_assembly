import os
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup, SoupStrainer
import configparser
import argparse

import logging
logging.basicConfig(level=logging.DEBUG)

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

    for link in BeautifulSoup(response.content, parse_only=SoupStrainer('a')):
        if link.has_attr('href') and link['href'].endswith(".jar") and "cromwell" in link['href']:
            return urljoin(base, link['href'])

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
    logging.info(f"Downloaded the latest release {filename}")
    
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
              

def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'([0-9]+)', text)]


def delete_older_releases(folder: str) -> None:
    # find all versions of cromwell
    versions = [filename for filename in os.listdir(folder) if "cromwell" in filename]
    
    # sort versions in descending order and delete older versions 
    versions.sort(key=natural_keys, reverse=True)
    older_releases = versions[1:]
    
    # delete older releases if any
    if older_releases:
        string_older_releases = ",".join(older_releases)
        logging.info(f"Older releases {string_older_releases} removed")
        for item in older_releases:
            os.remove(os.path.join(folder, item))
            

def setup_cromwell(url, save_dir):
    
    link = find_link(url)
    os.makedirs("cromwell", exist_ok=True)
    cromwell_dir = os.path.join(save_dir, "cromwell")
    filename = aria2c_download_file(link, cromwell_dir)
    cromwell_path = os.path.abspath(os.path.join(cromwell_dir, filename))
    modify_config_file("config.ini", 
                       section="cromwell", 
                       config_name="path", 
                       config_value=cromwell_path)
    delete_older_releases(cromwell_dir)
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_dir", metavar='', 
                        help='Directory to use for Cromwell download.')

    args = parser.parse_args()
    url = "https://github.com/broadinstitute/cromwell/releases/latest"
    setup_cromwell(url, args.save_dir)
    