version 1.0

# TODO: substitute sample id with basename function in .wdl
struct PairedSample {
    File file_r1
    File file_r2
    String sample_id
}

struct QcAndContigs { 
    File file_r1
    File file_r2
    File contigs
    String sample_id
}

struct QcFull { 
    File paired_r1
    File paired_r2
    File unpaired_r1
    File unpaired_r2
}
