from dataclasses import dataclass
from typing_extensions import Annotated
from datetime import datetime
from pathlib import Path
import json
import logging
import typer
from tqdm import tqdm
from Bio import Entrez
import agr_blast_service_configuration.schemas.metadata as agrdb

from .db_metadata import create_flybase_metadata

app = typer.Typer()

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "create_flybase_metadata.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
logger = logging.getLogger("generate_config")


@dataclass
class DefaultBlastDbConfiguration:
    contact: str = "iudev@morgan.harvard.edu"
    data_provider: str = "FB"
    date_produced: datetime = datetime.now()
    homepage_url: str = "https://flybase.org"
    logo_url: str = "https://flybase.org/images/fly_logo.png"
    public: bool = True
    organisms: Path = PROJECT_ROOT_DIR / "organisms.json"


DEFAULT_CONFIG = DefaultBlastDbConfiguration()


@app.command()
def generate_config(
    release: Annotated[str, typer.Option(help="The FlyBase release version")],
    contact: Annotated[
        type(DEFAULT_CONFIG.contact),
        typer.Option(help="Email of the FlyBase technical contact."),
    ] = DEFAULT_CONFIG.contact,
    data_provider: Annotated[
        type(DEFAULT_CONFIG.data_provider),
        typer.Option(help="The provider name assigned to FlyBase by the Alliance."),
    ] = DEFAULT_CONFIG.data_provider,
    date_produced: Annotated[
        type(DEFAULT_CONFIG.date_produced),
        typer.Option(help="The date this configuration file was produced."),
    ] = DEFAULT_CONFIG.date_produced,
    homepage_url: Annotated[
        type(DEFAULT_CONFIG.homepage_url),
        typer.Option(help="URL for FlyBase homepage."),
    ] = DEFAULT_CONFIG.homepage_url,
    logo_url: Annotated[
        type(DEFAULT_CONFIG.logo_url),
        typer.Option(help="URL for FlyBase logo."),
    ] = DEFAULT_CONFIG.logo_url,
    public: Annotated[
        type(DEFAULT_CONFIG.public), typer.Option(help="Public or private BLAST DB")
    ] = DEFAULT_CONFIG.public,
    ncbi_email: Annotated[
        str, typer.Option(help="Email to use when connecting to NCBI.")
    ] = DEFAULT_CONFIG.contact,
    organisms_file: Annotated[
        Path, typer.Option(help="Path to the organisms file.")
    ] = DEFAULT_CONFIG.organisms,
    output: Annotated[Path, typer.Option(help="Output configuration file.")] = None,
) -> None:
    if output is None:
        output = PROJECT_ROOT_DIR / "conf" / f"databases.{data_provider}.{release}.json"
        output.parent.mkdir(parents=True, exist_ok=True)

    Entrez.email = ncbi_email

    metadata = agrdb.Metadata(
        release=release,
        contact=contact,
        data_provider=data_provider,
        date_produced=date_produced,
        homepage_url=homepage_url,
        logo_url=logo_url,
        public=public,
    )
    all_dbs: list[agrdb.SequenceMetadata] = []

    for genus, species in tqdm(load_organisms(organisms_file)):
        if genus == "Drosophila" and species == "melanogaster":
            pass
        else:
            all_dbs.extend(create_flybase_metadata(genus, species))

    blast_dbs = agrdb.AgrBlastDatabases(metadata=metadata, data=all_dbs)
    with output.open("w") as outfile:
        json.dump(blast_dbs.to_dict(), outfile)


def load_organisms(organism_json: Path) -> list[list[str, str], ...]:
    """
    Load list of organisms from JSON file.

    :return: A list of lists of the form (genus, species) for each organism
    """
    with organism_json.open() as f:
        return json.load(f)


def main() -> None:
    app()


if __name__ == "__main__":
    app()
