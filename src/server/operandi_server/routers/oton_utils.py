from fastapi import HTTPException, status
from operandi_utils.oton import OTONConverter, OCRDValidator


async def validate_oton_with_handling(logger, ocrd_process_txt_path: str):
    try:
        # Separate validation for refined error logging
        validator = OCRDValidator()
        validator.validate(input_file=ocrd_process_txt_path)
    except ValueError as error:
        message = "Failed to validate the ocrd process workflow txt file"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


async def convert_oton_with_handling(
    logger, ocrd_process_txt_path: str, nf_script_dest_path: str, environment: str, with_mets_server: bool
):
    environments = ["local", "docker", "apptainer"]
    if environment not in environments:
        message = f"Unknown environment value: {environment}. Must be one of: {environments}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    try:
        converter = OTONConverter()
        converter.convert_oton(str(ocrd_process_txt_path), str(nf_script_dest_path), environment, with_mets_server)
    except ValueError as error:
        message = "Failed to convert ocrd process workflow to nextflow workflow"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
