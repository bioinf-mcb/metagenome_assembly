workflow metaphlan {

	call run_metaphlan

}

task run_metaphlan {
	File fastq_R1
	File fastq_R2
	File fastq_S1
	File fastq_S2
	String sample_id

	command {


		metaphlan --input_type fastq \
                  --add_viruses \
                  --unknown_estimation \
                  --samout ${sample_id}.sam \
                  --bowtie2out ${sample_id}.bowtie2.out \
                  ${fastq_R1},${fastq_R2},${fastq_S1},${fastq_S2} \
                  ${sample_id}.metaphlan.tsv

        samtools view -bS ${sample_id}.sam -o ${sample_id}.bam
        gzip ${sample_id}.bowtie2.out
    }
    
    output {
    	File metaphlan_out_tsv = "${sample_id}.metaphlan.tsv"
    	File metaphlan_out_bam = "${sample_id}.bam"
    	File metaphlan_out_bowtie2 = "${sample_id}.bowtie2.out.gz"
    }
	
	runtime {
		docker: "gcr.io/osullivan-lab/metaphlan:v3.0.12"
		cpu: 1
  		memory: "8GB"
  		preemptible: 2
        maxRetries: 3
        zones: "us-central1-a us-central1-b us-central1-c us-central1-f"
  		disks: "local-disk 50 HDD"
	}

}
