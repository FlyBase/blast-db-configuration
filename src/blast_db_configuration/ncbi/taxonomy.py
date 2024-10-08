from functools import cache
from typing import Optional
import logging
from Bio import Entrez

logger = logging.getLogger(__name__)


@cache
def get_taxonomy_id(genus: str, species: str) -> Optional[int]:
    """
    Get NCBI taxonomy ID for a given genus and species.
    :param genus: Genus name.
    :param species: Species name.
    :return: NCBI taxonomy ID.
    """
    try:
        logger.debug("Searching for %s %s", genus, species)
        handle = Entrez.esearch(db="taxonomy", term=f"{genus} {species}[SCIN]")
        record = Entrez.read(handle)
        handle.close()
        num_results = int(record["Count"])
        if num_results == 1:
            return int(record["IdList"][0])
        elif num_results > 1:
            raise ValueError(f"{num_results} results found for {genus} {species}")
    except IOError as ioe:
        logger.error(ioe)
    return None
