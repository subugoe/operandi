from operandi_utils.oton.parser import OCRDParser, ProcessorCallArguments


def test_parse_arguments_basic():
    processor_command: str = "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN"
    processor_call_arguments: ProcessorCallArguments = OCRDParser.parse_arguments(processor_command)
    assert processor_call_arguments.executable == "ocrd-cis-ocropy-binarize"
    assert processor_call_arguments.input_file_grps == "OCR-D-IMG"
    assert processor_call_arguments.output_file_grps == "OCR-D-BIN"
    assert processor_call_arguments.mets_file_path == "./mets.xml"
    assert processor_call_arguments.parameters == {}


def test_parse_arguments_basic_with_mets():
    processor_command: str = """cis-ocropy-binarize -m "/dummy/path" -I OCR-D-IMG -O OCR-D-BIN"""
    processor_call_arguments: ProcessorCallArguments = OCRDParser.parse_arguments(processor_command)
    assert processor_call_arguments.executable == "ocrd-cis-ocropy-binarize"
    assert processor_call_arguments.input_file_grps == "OCR-D-IMG"
    assert processor_call_arguments.output_file_grps == "OCR-D-BIN"
    assert processor_call_arguments.mets_file_path == "/dummy/path"
    assert processor_call_arguments.parameters == {}


def test_parse_arguments_with_params_separated():
    processor_command: str = "calamari-recognize -I OCR-D-INPUT -O OCR-D-OCR -P checkpoint_dir qurator-gt4histocr-1.0 -P dummy dummy"
    processor_call_arguments: ProcessorCallArguments = OCRDParser.parse_arguments(processor_command)
    assert processor_call_arguments.executable == "ocrd-calamari-recognize"
    assert processor_call_arguments.input_file_grps == "OCR-D-INPUT"
    assert processor_call_arguments.output_file_grps == "OCR-D-OCR"
    assert processor_call_arguments.mets_file_path == "./mets.xml"
    assert processor_call_arguments.parameters == {"checkpoint_dir": "qurator-gt4histocr-1.0", "dummy": "dummy"}


def test_parse_arguments_with_params_clustered():
    processor_command: str = """
    calamari-recognize -I OCR-D-INPUT -O OCR-D-OCR -p '{"checkpoint_dir": "qurator-gt4histocr-1.0", "dummy": "dummy"}'
    """
    processor_call_arguments: ProcessorCallArguments = OCRDParser.parse_arguments(processor_command)
    assert processor_call_arguments.executable == "ocrd-calamari-recognize"
    assert processor_call_arguments.input_file_grps == "OCR-D-INPUT"
    assert processor_call_arguments.output_file_grps == "OCR-D-OCR"
    assert processor_call_arguments.mets_file_path == "./mets.xml"
    assert processor_call_arguments.parameters == {"checkpoint_dir": "qurator-gt4histocr-1.0", "dummy": "dummy"}
