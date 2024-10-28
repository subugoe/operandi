import click
from .converter import Converter
from .validators.ocrd_validator import OCRDValidator


@click.group()
def cli():
    pass


@cli.command("convert", help="Convert an OCR-D workflow to a Nextflow workflow script.")
@click.option('-I', '--input_path', type=click.Path(dir_okay=False, exists=True, readable=True),
              show_default=True, help='Path to the OCR-D workflow file to be converted.')
@click.option('-O', '--output_path', type=click.Path(dir_okay=False, writable=True),
              show_default=True, help='Path of the Nextflow workflow script to be generated.')
@click.option('-D', '--dockerized', is_flag=True,
              help='If set, then the dockerized variant of the Nextflow script is generated.')
def convert(input_path: str, output_path: str, dockerized: bool):
    print(f"Converting from: {input_path}")
    print(f"Converting to: {output_path}")
    Converter().convert_OtoN(input_path, output_path, dockerized)
    print("Conversion was successful!")


@cli.command("validate", help="Validate an OCR-D workflow txt file.")
@click.option('-I', '--input_path', show_default=True,
              help='Path to the OCR-D workflow file to be validated.')
def validate(input_path: str):
    OCRDValidator().validate(input_path)
    print(f"Validating: {input_path}")
    print("Validation was successful!")
