import os 

bowtie2_index_formats = [
    ".1.bt2", ".2.bt2", ".3.bt2", ".4.bt2", ".rev.1.bt2", ".rev.2.bt2"
    ]
grch38_url = "https://genome-idx.s3.amazonaws.com/bt/GRCh38_noalt_as.zip"

kneaddata_config = "./cromwell_configs/kneaddata.conf"
output_config = "./json_templates/output_options.json"
cromwell_dir = ""
wdl_paths = {
    "qc_and_assemble" : "./wdl/qc_and_assemble.wdl",
}