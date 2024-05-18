import ftplib
import logging
import re
import urllib.error
from pathlib import Path
from functools import cache
from ftplib import FTP
from typing import Iterator, Optional
from enum import StrEnum
from Bio import Entrez

logger = logging.getLogger(__name__)

FTP_HOST = "ftp.ncbi.nlm.nih.gov"

FtpDirectoryListing = list[tuple[str, dict[str, str]]]

FTP_FILES_CACHE: dict[str, FtpDirectoryListing] = {}


class OrganismGroup(StrEnum):
    """
    Organism groups used by the NCBI RefSeq genomes FTP server directory structure.
    see https://ftp.ncbi.nlm.nih.gov/genomes/refseq/
    """

    ARCHAEA = "archaea"
    BACTERIA = "bacteria"
    FUNGI = "fungi"
    INVERTEBRATE = "invertebrate"
    METAGENOMES = "metagenomes"
    MITOCHONDRIA = "mitochondria"
    PLANT = "plant"
    PLASMID = "plasmid"
    PLASTID = "plastid"
    PROTOZOA = "protozoa"
    VERTEBRATE_MAMMALIAN = "vertebrate_mammalian"
    VERTEBRATE_OTHER = "vertebrate_other"
    VIRAL = "viral"


def get_current_genome_assembly_files(
    genus: str,
    species: str,
    email: str,
    organism_group: str | OrganismGroup = OrganismGroup.INVERTEBRATE,
    file_regex: str = None,
) -> Optional[tuple[str, str, str]]:
    """
    Get the current genome assembly directory for a given organism.

    :param genus: Genus of organism
    :param species: Species of organism
    :param email: Email to use for the anonymous FTP connection password
    :param organism_group: Organism group (default: 'invertebrate', see above)
    :param file_regex: Regular expression to match files (default: None)
    :return: Tuple of (genome assembly directory, genome assembly file, md5 checksum file)
    """
    if type(organism_group) is str:
        organism_group = OrganismGroup(organism_group)

    path = f"/genomes/refseq/{organism_group}/{genus}_{species.replace(' ', '_')}/latest_assembly_versions"
    with FTP(FTP_HOST, timeout=30) as ftp:
        # Use a passive connection to avoid firewall blocking and login.
        ftp.set_pasv(True)
        ftp.login(user="anonymous", passwd=email)
        # Get a list of files in the directory.
        try:
            files = ftp.mlsd(path)
            # Look for the latest genome assembly directory.
            directories = filter_ftp_paths(files, "^GC[AF]_")
        except ftplib.error_perm as e:
            if "No such file or directory" in str(e):
                # TODO - query NCBI for latest assembly
                # logger.info(f"No genome assembly found at {path}, querying NCBI for latest assembly.")
                # search_ncbi_assemblies(genus, species)
                logger.error(f"FTP error: {e}")
                return None
            else:
                logger.error(f"FTP error: {e}")
                return None
        except ftplib.all_errors as e:
            logger.error(f"FTP error while processing {genus} {species}: {e}")
            return None

        if len(directories) >= 1:
            if len(directories) > 1:
                logger.warning(
                    "Found multiple genome assemblies in the 'latest' directory, using the first one: %s",
                    ", ".join(directories),
                )
            assembly_dir = directories[0]
            # Get a list of files in the latest genome assembly directory.
            try:
                assembly_ftp_dir = f"{path}/{assembly_dir}"
                assembly_files = FTP_FILES_CACHE.get(assembly_ftp_dir)
                if assembly_files is None:
                    assembly_files = [
                        file for file in ftp.mlsd(f"{path}/{assembly_dir}")
                    ]
                    FTP_FILES_CACHE[assembly_ftp_dir] = assembly_files
                # Filter files based on the regular expression filter.
                filtered_files = filter_ftp_paths(assembly_files, file_regex)
            except ftplib.all_errors as e:
                logger.error(f"FTP error while processing {genus} {species}: {e}")
                return None

            files_with_md5 = []
            checksums = {}

            # Look for the md5 of the genome assembly file.

            try:

                def get_md5sum(line: str) -> str:
                    checksum, remote_file = re.split(r"\s+", line)
                    remote_file = Path(remote_file).name
                    checksums[remote_file] = checksum

                ftp.retrlines(
                    f"RETR {path}/{assembly_dir}/md5checksums.txt",
                    callback=get_md5sum,
                )
            except ftplib.all_errors as e:
                logger.error("Failed to get md5 checksums:\n%s", str(e))

            for file in filtered_files:
                if file in checksums:
                    md5sum = checksums[file]
                    files_with_md5.append(
                        (
                            assembly_dir,
                            f"ftp://{FTP_HOST}{path}/{assembly_dir}/{file}",
                            md5sum,
                        )
                    )

                # Make sure we only found one checksum.
                if len(files_with_md5) > 1:
                    logger.warning(
                        "Found multiple files with MD5 checksums, using the first one"
                    )
                elif len(files_with_md5) == 0:
                    logger.warning("Could not find MD5 checksum for file")

            return files_with_md5[0] if len(files_with_md5) >= 1 else None

        else:
            logger.error(f"No genome assembly directory found for {genus} {species}")
            return None


@cache
def search_ncbi_assemblies(genus: str, species: str) -> list[str]:
    try:
        assembly_query = f"({genus} {species}[Organism]) AND (latest[filter] AND all[filter] NOT anomalous[filter])"
        assembly_handle = Entrez.esearch(db="assembly", term=assembly_query)
        assembly_records = Entrez.read(assembly_handle)
        num_results = int(assembly_records.get("Count", 0))
        if num_results == 0:
            return []
        else:
            efetch_handle = Entrez.efetch(
                db="assembly", id=",".join(assembly_records["IdList"])
            )
            efetch_records = Entrez.read(efetch_handle)
            print(efetch_records)
    except IOError as ioe:
        logger.error(ioe)
    finally:
        assembly_handle.close()
        efetch_handle.close()
    return None


def filter_ftp_paths(
    files: Iterator[FtpDirectoryListing], file_regex: str = None
) -> list[str]:
    """
    Given an iterator for files from the `mlsd` FTP command, filter the files based on the regular expression.

    :param files: Iterator for the files from the `mlsd` FTP command
    :param file_regex: Regular expression to match files (default: None)
    :return: List of files that match the regular expression
    """
    ftp_paths = []
    pattern = re.compile(file_regex) if file_regex else None
    for filename, facts in files:
        if pattern.search(filename.strip()):
            logger.debug(f"Found {filename}")
            ftp_paths.append(filename)
    return ftp_paths
