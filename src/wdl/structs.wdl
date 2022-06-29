version 1.0

struct PairedSample {
    File file_r1
    File file_r2
}

struct QcAndContigs { 
    File file_r1
    File file_r2
    File contigs
}

struct QcFull { 
    File paired_r1
    File paired_r2
    File unpaired_r1
    File unpaired_r2
}
