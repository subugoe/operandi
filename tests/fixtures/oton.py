from pytest import fixture
from operandi_utils.oton import OTONConverter, OCRDValidator, OCRDParser


@fixture(scope="package", name="oton_converter")
def fixture_oton_converter():
    return OTONConverter()

@fixture(scope="package", name="ocrd_validator")
def fixture_ocrd_validator():
    return OCRDValidator()

@fixture(scope="package", name="ocrd_parser")
def fixture_ocrd_parser():
    return OCRDParser()
