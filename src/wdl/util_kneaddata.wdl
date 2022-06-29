version 1.0

workflow read_table {
    input {
	    Array[File] logs
    }

	call countTable {
	    input:
        logFiles = logs
	}
}

task countTable {
    input{
    Array[File] logFiles
    }
    
    command {
        
        cat ${write_lines(logFiles)} > logFiles.txt
        mkdir dir_logfiles
        xargs -a logFiles.txt mv -t dir_logfiles/
        
        kneaddata_read_count_table --input dir_logfiles/ --output kneaddata_read_count_table.tsv

    }

    output {
        File kneaddataReadCountTable = "kneaddata_read_count_table.tsv"
    }

    runtime {
        docker: "crusher083/kneaddata@sha256:db19f5146938b1bf806722df7a68594b1536cb25612a941be1556205abffb9f6" # use kneaddata docker 
        maxRetries: 1
    }
}