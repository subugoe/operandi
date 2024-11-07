import click
from operandi_utils.oton.oton_converter import OTONConverter
from operandi_utils.oton.ocrd_validator import OCRDValidator


@click.group()
def cli():
    pass


@cli.command("convert", help="Convert an OCR-D workflow to a Nextflow workflow script.")
@click.option('-I', '--input_path', type=click.Path(dir_okay=False, exists=True, readable=True),
              show_default=True, help='Path to the OCR-D workflow file to be converted.')
@click.option('-O', '--output_path', type=click.Path(dir_okay=False, writable=True),
              show_default=True, help='Path of the Nextflow workflow script to be generated.')
@click.option('-E', '--environment', type=str, default="local",
              help='The environment of the output Nextflow file. One of: local, docker, apptainer.')
@click.option('-M', '--with_mets_server', type=bool, default=False,
              help='Whether the Nextflow file will use a mets server or not. '
                   'If a Mets server is not used, then splitting and merging the mets files will be used.')
def convert(input_path: str, output_path: str, environment: str, with_mets_server):
    print(f"Converting from: {input_path}")
    print(f"Converting to: {output_path}")
    environments = ["local", "docker", "apptainer"]
    if environment not in environments:
        print(f"Invalid environment value: {environment}. Must be one of: {environments}")
        exit(1)
    OTONConverter().convert_oton(input_path, output_path, environment, with_mets_server)
    print(f"Success: Converting workflow from ocrd process to Nextflow with {environment} processor calls. "
          f"The Nextflow workflow will utilize a mets server: {with_mets_server}")


@cli.command("validate", help="Validate an OCR-D workflow txt file.")
@click.option('-I', '--input_path', show_default=True, help='Path to the OCR-D workflow file to be validated.')
def validate(input_path: str):
    OCRDValidator().validate(input_path)
    print(f"Validating: {input_path}")
    print("Validation was successful!")
