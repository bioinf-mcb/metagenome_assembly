workflow qc_and_assemble {

    call assemble 

}

task assemble {
    File r1
    File r2
    File s1
    File s2
    String sample

    command <<<
        rm -f assemble
        megahit -1 ${r1} -2 ${r2} -r ${s1},${s2} -t 4 -m 15000000000 -o assemble
        cat assemble/final.contigs.fa | \
        awk -v var="${sample}" '
            {if($0 ~ /^>/) {contigName=substr($0, 2,length($0))} 
            else {seq=$0; if(length($0) >= 500) {print ">"var"_"contigName"\n"seq}} }' > assemble/${sample}.min500.contigs.fa
    >>>

    output {
        File fileContigs = "assemble/${sample}.min500.contigs.fa"
    
}   runtime {
        docker: "gcr.io/microbiome-xavier/metagenomicstools:081518"
        cpu: 4
        memory: "15GB"
        preemptible: 2
        maxRetries: 3
        disks: "local-disk 100 SSD"
    }
}
