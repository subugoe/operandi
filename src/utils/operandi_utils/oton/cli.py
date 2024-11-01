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
def convert(input_path: str, output_path: str, environment: str):
    print(f"Converting from: {input_path}")
    print(f"Converting to: {output_path}")
    if environment == "local":
        OTONConverter().convert_oton_env_local(input_path, output_path)
    elif environment == "docker":
        OTONConverter().convert_oton_env_docker(input_path, output_path)
    elif environment == "apptainer":
        OTONConverter().convert_oton_env_apptainer(input_path, output_path)
    else:
        print("Unspecified environment type. Must be one of: local, docker, apptainer.")
        exit(1)
    print(f"Success: Converting workflow from ocrd process to Nextflow with {environment} processor calls")


@cli.command("validate", help="Validate an OCR-D workflow txt file.")
@click.option('-I', '--input_path', show_default=True, help='Path to the OCR-D workflow file to be validated.')
def validate(input_path: str):
    OCRDValidator().validate(input_path)
    print(f"Validating: {input_path}")
    print("Validation was successful!")
