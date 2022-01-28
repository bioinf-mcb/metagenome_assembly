workflow predict_mags {

	call kneaddataReadCountTable {
	    input:
	    logFiles=kneadData.log_file
	}
}

task kneaddataReadCountTable {
    Array[String] logFiles

    command {
        
        cat ${write_lines(logFiles)} > logFiles_2_download.txt
        mkdir dir_logfiles
        cat logFiles_2_download.txt | gsutil -m cp -I dir_logfiles/
        
        kneaddata_read_count_table --input dir_logfiles/ --output kneaddata_read_count_table.tsv

    }

    output {
        File kneaddataReadCountTable = "kneaddata_read_count_table.tsv"
    }

    runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:101419" # use kneaddata docker 
        maxRetries: 2
    }
}