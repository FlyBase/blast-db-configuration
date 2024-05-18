import logging

import agr_blast_service_configuration.schemas.metadata as blast_metadata_schema

from .ncbi import taxonomy as tax
from .ncbi import genomes as genomes

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


def create_dmel_metadata():
    pass
    # dbs.extend(
    #     [
    #         blast_metadata.BlastDBMetaData(
    #             version=options.dmel_annot,
    #             URI=f"ftp://ftp.flybase.org/genomes/Drosophila_melanogaster/dmel_r{options.dmel_annot}_{options.release}/fasta/dmel-all-chromosome-r{options.dmel_annot}.fasta.gz",
    #             md5sum="b7bc17acfd655914c68326df8599a9ca",  # TODO - Hard coded for now, need to fetch this from the MD5SUM file
    #             genus="Drosophila",
    #             species="melanogaster",
    #             blast_title=f"D. melanogaster Genome Assembly ({options.dmel_annot})",
    #             description="Drosophila melanogaster genome assembly",
    #             taxon_id="NCBITaxon:7227",
    #             seqtype="nucl",
    #         ),
    #         blast_metadata.BlastDBMetaData(
    #             version=options.dmel_annot,
    #             URI=f"ftp://ftp.flybase.org/genomes/Drosophila_melanogaster/dmel_r{options.dmel_annot}_{options.release}/fasta/dmel-all-translation-r{options.dmel_annot}.fasta.gz",
    #             # TODO - Hard coded for now, need to fetch this from the MD5SUM file
    #             md5sum="e3f959ab0e1026de56e1bd00490450e5",
    #             genus="Drosophila",
    #             species="melanogaster",
    #             blast_title=f"D. melanogaster Protein Sequences ({options.dmel_annot})",
    #             description="Drosophila melanogaster protein sequences",
    #             taxon_id="NCBITaxon:7227",
    #             seqtype="prot",
    #         ),
    #     ]
    # )
    # flybase_blast_metadata = blast_metadata.AGRBlastDatabases(
    #     metaData=blast_metadata.AGRBlastMetadata(
    #         contact=options.email, dataProvider="FlyBase", release=options.release
    #     ),
    #     data=dbs,
    # )
    # print(flybase_blast_metadata.json())
