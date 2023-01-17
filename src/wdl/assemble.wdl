workflow metagenome_assy {
    Array[File] input_files

    String bbtools_container="microbiomedata/bbtools:38.96"
    String spades_container="bryce911/spades:3.15.2"
    String megahit_container="crusher083/megahit"
    String assembler = "megahit"
    Int threads = 8
    Int min_contig_len = 500
    String outdir

    scatter(file in input_files){
        call bbcms {
            input: reads_file=file, container=bbtools_container
        }
        if (assembler == "spades") {
            call assemble_spades {
                input: infile1=bbcms.out1, infile2=bbcms.out2, container=spades_container, threads=threads
            }
        }
        if (assembler == "megahit") {
            call assemble_megahit {
                input: infile1=bbcms.out1, infile2=bbcms.out2, container=megahit_container, threads=threads
            }

        }
        call create_agp {
            input: scaffolds_in=if (assembler == "spades") then assemble_spades.out else assemble_megahit.out,
            min_contig_len=min_contig_len,
            container=bbtools_container
        }
    }

    output {
        Array[File] final_contigs = create_agp.outcontigs
        Array[File] final_scaffolds = create_agp.outscaffolds
        Array[File?] final_spades_log = if (assembler == "spades") then assemble_spades.outlog else assemble_megahit.outlog
	    Array[File] final_readlen = bbcms.outreadlen
	    Array[File] final_counts = bbcms.outcounts
    }
}

task bbcms{
    File reads_file

    String container

    String filename_counts="counts.metadata.json"

    String filename_outfile="input.corr.fastq.gz"
    String filename_outfile1="input.corr.left.fastq.gz"
    String filename_outfile2="input.corr.right.fastq.gz"

     String filename_readlen="readlen.txt"
     String filename_outlog="stdout.log"
     String filename_errlog="stderr.log"
     String filename_kmerfile="unique31mer.txt"

     String java="-Xmx40g"
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

task assemble_spades{
    File infile1
    File infile2

    Int threads
    String container

    String outprefix="spades3"
    String filename_outfile="${outprefix}/scaffolds.fasta"
    String filename_spadeslog ="${outprefix}/spades.log"
    String dollar="$"

    runtime {docker: container}

    command{
       spades.py -m 2000 --tmp-dir ${dollar}PWD -o ${outprefix} --only-assembler -k 33,55,77,99,127 --meta -t ${threads} -1 ${infile1} -2 ${infile2}
    }

    output {
           File out = filename_outfile
           File outlog = filename_spadeslog
    }
}


task assemble_megahit{
    File infile1
    File infile2

    Int threads
    String container

    String outprefix="megahit"
    String filename_outfile="${outprefix}/final.contigs.fa"
    String filename_megahitlog ="megahit.log"
    String dollar="$"
    runtime {docker: container}

    command{
        megahit -1 ${infile1} -2 ${infile2} -t ${threads} -m 0.6 -o ${outprefix} 2>> ${filename_megahitlog}
    }

    output {
           File out = filename_outfile
           File outlog = filename_megahitlog
    }

}

task create_agp {
    File scaffolds_in
    String container
    Int min_contig_len
    String prefix="assembly"

    String filename_contigs="${prefix}.min${min_contig_len}.contigs.fa"
    String filename_scaffolds="${prefix}.scaffolds.fasta"
    String filename_agp="${prefix}.agp"
    String filename_legend="${prefix}.scaffolds.legend"
    String java="-Xmx40g"

    runtime {docker: container}


    command{
        fungalrelease.sh ${java} in=${scaffolds_in} out=${filename_scaffolds} \
        outc=${filename_contigs} agp=${filename_agp} legend=${filename_legend} \
        mincontig=${min_contig_len} minscaf=${min_contig_len} sortscaffolds=t sortcontigs=t overwrite=t
    }
    output{
        File outcontigs = filename_contigs
        File outscaffolds = filename_scaffolds
        File outagp = filename_agp
        File outlegend = filename_legend
    }
}


task make_output{
    String outdir
    Array[File] outcontigs
    Array[File] outscaffolds
    Array[File] outagp
    Array[File] outlegend
    String dollar ="$"

    command<<<
        mkdir -p ${outdir}
        for i in ${sep=' ' outcontigs}
        do
            f=${dollar}(basename $i)
            dir=${dollar}(dirname $i)
            prefix=${dollar}{f%.anqdpht*}
            mkdir -p ${outdir}/$prefix
            cp -f $dir/../filtered/filterStats.txt ${outdir}/$prefix
            cp -f $dir/../filtered/filterStats2.txt ${outdir}/$prefix
            cp -f $dir/../filtered/filterStats.json ${outdir}/$prefix
            cp -f $i ${outdir}/$prefix
            echo ${outdir}/$prefix/$f
        done
        chmod 755 -R ${outdir}
    >>>

    output{
        Array[String] fastq_files = read_lines(stdout())
    }
}