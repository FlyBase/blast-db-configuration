import logging
import urllib.request

import agr_blast_service_configuration.schemas.metadata as blast_metadata_schema

from .ncbi import genomes as genomes
from .ncbi import taxonomy as tax

logger = logging.getLogger(__name__)


def create_metadata_from_ncbi(
    genus: str, species: str, email: str
) -> list[blast_metadata_schema.SequenceMetadata]:
    """
    Create the BLAST Database metadata schema using NCBI FTP and API services.

    :param genus: Genus name
    :param species: Species name
    :param email: Email address to use for connecting to the NCBI
    :return: BLAST Database metadata schemas
    """
    dbs: list[blast_metadata_schema.SequenceMetadata] = []
    assembly_targets = [
        {
            "file_regex": "(?<!_from)_genomic.fna.gz$",
            "blast_title": "{}. {} Genome Assembly ({})",
            "description": "{} {} genome assembly",
            "seqtype": "nucl",
        },
        {
            "file_regex": "_rna.fna.gz$",
            "blast_title": "{}. {} RNA Sequences ({})",
            "description": "{} {} RNA sequences",
            "seqtype": "nucl",
        },
        {
            "file_regex": "_protein.faa.gz$",
            "blast_title": "{}. {} Protein Sequences ({})",
            "description": "{} {} protein sequences",
            "seqtype": "prot",
        },
    ]
    for target in assembly_targets:
        assembly_files = genomes.get_current_genome_assembly_files(
            genus,
            species,
            file_regex=target["file_regex"],
            email=email,
            organism_group=genomes.OrganismGroup.INVERTEBRATE,
        )
        if not assembly_files:
            logger.error(f"No assembly files found for {genus} {species}")
            continue

        # Get taxonomy ID.
        taxid = tax.get_taxonomy_id(genus, species)
        dbs.append(
            blast_metadata_schema.SequenceMetadata(
                version=assembly_files[0],
                uri=assembly_files[1],
                md5_sum=assembly_files[2],
                genus=genus,
                species=species,
                blast_title=target["blast_title"].format(
                    genus[0], species, assembly_files[0]
                ),
                description=target["description"].format(genus, species),
                taxon_id=str(taxid),
                seqtype=blast_metadata_schema.BlastDBType(target["seqtype"]),
            )
        )
    return dbs


def create_dmel_metadata(
    dmel_annot_release: str, release: str
) -> list[blast_metadata_schema.SequenceMetadata]:
    """
    Generate a list of BLAST DB metadata schemas based on Dmel annot release.

    :param dmel_annot_release: The Dmel annot release
    :param release: The FlyBase release
    :return: List of BLAST DB metadata schemas
    """
    dmel_dbs = [
        {
            "uri": "https://s3ftp.flybase.org/alliance/blast/dmel-assembly.fasta.gz",
            "description": f"D. melanogaster Genome Assembly {dmel_annot_release}",
            "seqtype": blast_metadata_schema.BlastDBType.NUCL,
            "md5_sum": None,
            "genome_browser": blast_metadata_schema.GenomeBrowser(
                assembly="Drosophila_melanogaster",
                data_url=f"https://s3.amazonaws.com/agrjbrowse/MOD-jbrowses/FlyBase/{release}/d_melanogaster/",
                gene_track="Curated Genes",
                mod_gene_url="https://flybase.org/reports/",
                tracks=[
                    "Drosophila_melanogaster_all_genes",
                    "Drosophila_melanogaster_ht_variants",
                    "Drosophila_melanogaster_variants",
                    "Drosophila_melanogaster_multiple-variant_alleles",
                ],
                type=blast_metadata_schema.GenomeBrowseType.JBROWSE,
                url="https://flybase.org/jbrowse/?data=data/json/dmel",
            ),
        },
        {
            "uri": "https://s3ftp.flybase.org/alliance/blast/dmel-intergenic.fasta.gz",
            "description": f"D. melanogaster Intergenic Regions {dmel_annot_release}",
            "seqtype": blast_metadata_schema.BlastDBType.NUCL,
            "md5_sum": None,
        },
        {
            "uri": "https://s3ftp.flybase.org/alliance/blast/dmel-transcript.fasta.gz",
            "description": f"D. melanogaster Transcripts {dmel_annot_release}",
            "seqtype": blast_metadata_schema.BlastDBType.NUCL,
            "md5_sum": None,
        },
        {
            "uri": "https://s3ftp.flybase.org/alliance/blast/dmel-translation.fasta.gz",
            "description": f"D. melanogaster Proteins {dmel_annot_release}",
            "seqtype": blast_metadata_schema.BlastDBType.PROT,
            "md5_sum": None,
        },
        {
            "uri": "https://s3ftp.flybase.org/alliance/blast/dmel-transposon.fasta.gz",
            "description": f"D. melanogaster Transposons {dmel_annot_release}",
            "seqtype": blast_metadata_schema.BlastDBType.NUCL,
            "md5_sum": None,
        },
    ]
    checksums = fetch_dmel_checksums(
        "https://s3ftp.flybase.org/alliance/blast/md5sum.txt"
    )
    for db in dmel_dbs:
        uri = db.get("uri")
        key = uri[uri.rfind("/") + 1 :]
        db["md5_sum"] = checksums.get(key)

    return [
        blast_metadata_schema.SequenceMetadata(
            version=dmel_annot_release,
            uri=db.get("uri"),
            md5_sum=db.get("md5_sum"),
            genus="Drosophila",
            species="melanogaster",
            blast_title=db.get("description"),
            description=db.get("description"),
            taxon_id="7227",
            seqtype=db.get("seqtype"),
            genome_browser=db.get("genome_browser"),
        )
        for db in dmel_dbs
    ]


def fetch_dmel_checksums(uri: str) -> dict[str, str]:
    """
    Get the current Dmel FASTA checksums.

    :param uri: The URI of the checksum file
    :return: The text content of the checksum file
    """
    checksums = {}
    with urllib.request.urlopen(uri) as response:
        md5_lines = response.read().decode("utf-8").splitlines()
        for line in md5_lines:
            md5, filename = line.split()
            checksums[filename] = md5
    return checksums
