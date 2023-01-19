workflow metagenome_assy {
    Array[File] input_files

    String bbtools_container="microbiomedata/bbtools:38.96"
    String spades_container="bryce911/spades:3.15.2"
    String megahit_container="crusher083/megahit"
    String assembler = "megahit"
    Int threads = 24
    Int min_contig_len = 500

    scatter(file in input_files){
        call bbcms {
            input: reads_file=file, container=bbtools_container
        }
        if (assembler == "megahit") {
            call assemble_megahit {
                input: infile1=bbcms.out1, infile2=bbcms.out2, container=megahit_container, threads=threads
            }

        }
        call create_agp {
            input: scaffolds_in=assemble_megahit.out,
            min_contig_len=min_contig_len,
            container=bbtools_container
        }
    }

    output {
        Array[File] final_contigs = create_agp.outcontigs
        Array[File] final_scaffolds = create_agp.outscaffolds
    }
}

task bbcms{
    File reads_file

    String container

    String filename_counts="counts.metadata.json"
    String prefix = basename(reads_file, ".anqdpht.fastq.gz")
    String filename_outfile="${prefix}.corr.fastq.gz"
    String filename_outfile1="${prefix}.corr.left.fastq.gz"
    String filename_outfile2="${prefix}.corr.right.fastq.gz"

    String filename_readlen="${prefix}.readlen.txt"
    String filename_outlog="${prefix}.stdout.log"
    String filename_errlog="${prefix}.stderr.log"
    String filename_kmerfile="${prefix}.unique31mer.txt"

    String java="-Xmx30g"
    String awk="{print $NF}"

    runtime {docker: container}

    command {

    touch ${filename_readlen}

    readlength.sh -Xmx1g in=${reads_file} out=${filename_readlen} overwrite
        bbcms.sh ${java} metadatafile=${filename_counts} mincount=2 highcountfraction=0.6 \
        in=${reads_file} out1=${filename_outfile1} out2=${filename_outfile2} \
        1> ${filename_outlog} 2> ${filename_errlog}
    reformat.sh in1=${filename_outfile1} in2=${filename_outfile2} out=${filename_outfile}
    grep Uniq ${filename_errlog} | awk '${awk}' > ${filename_kmerfile}
    }

    output {
            File out = filename_outfile
            File out1 = filename_outfile1
            File out2 = filename_outfile2
            File outreadlen = filename_readlen
            File stdout = filename_outlog
            File stderr = filename_errlog
            File outcounts = filename_counts
	        String kmers = read_string(filename_kmerfile)
    }

}


task assemble_megahit{
    File infile1
    File infile2

    Int threads
    String container

    String outprefix=basename(infile1, ".corr.left.fastq.gz")
    String filename_outfile="${outprefix}.final.contigs.fa"
    String filename_megahitlog ="megahit.log"
    String dollar="$"
    runtime {docker: container}

    command<<<
        megahit -1 ${infile1} -2 ${infile2} -t ${threads} -m 0.6 -o ${outprefix} 2>> ${filename_megahitlog} && \
        mv ${outprefix}/final.contigs.fa ${outprefix}.final.contigs.fa
    >>>

    output {
           File out = filename_outfile
           File outlog = filename_megahitlog
           String prefix = outprefix
    }

}

task create_agp {
    File scaffolds_in
    String container
    Int min_contig_len
    String prefix = basename(scaffolds_in, ".final.contigs.fa")

    String filename_contigs="${prefix}.min${min_contig_len}.contigs.fa"
    String filename_scaffolds="${prefix}.scaffolds.fasta"
    String filename_agp="${prefix}.agp"
    String filename_legend="${prefix}.scaffolds.legend"
    String java="-Xmx30g"
    String dollar="$"

    runtime {docker: container}


    command<<<
        fungalrelease.sh ${java} in=${scaffolds_in} out=${filename_scaffolds} \
        outc=${filename_contigs} agp=${filename_agp} legend=${filename_legend} \
        mincontig=${min_contig_len} minscaf=${min_contig_len} sortscaffolds=t sortcontigs=t overwrite=t \
        && export dir=${dollar}(dirname ${scaffolds_in}) \
        && mkdir -p ${dollar}{dir} \
        && cp ${filename_contigs} ${dollar}{dir} \
        && cp ${filename_scaffolds} ${dollar}{dir}
    >>>
    output{
        File outcontigs = filename_contigs
        File outscaffolds = filename_scaffolds
        File outagp = filename_agp
        File outlegend = filename_legend
    }
}