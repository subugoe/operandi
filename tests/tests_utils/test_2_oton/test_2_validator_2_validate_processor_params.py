from pytest import raises
from operandi_utils.oton import ProcessorCallArguments


def test_correctness_basic(ocrd_parser, ocrd_validator):
    call_args: ProcessorCallArguments = ocrd_parser.parse_arguments(
        "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN")
    ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=False)
    assert call_args.parameters == {}
    ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=True)
    assert len(call_args.parameters) > 0


def test_correctness_with_params_separated(ocrd_parser, ocrd_validator):
    call_args: ProcessorCallArguments = ocrd_parser.parse_arguments(
        "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN -P dpi 177.0 -P threshold 0.42")
    ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=False)
    assert call_args.parameters == {"dpi": 177.0, "threshold": 0.42}
    ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=True)
    assert len(call_args.parameters) > 2


def test_correctness_with_params_clustered(ocrd_parser, ocrd_validator):
    call_args: ProcessorCallArguments = ocrd_parser.parse_arguments(
        """cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN -p '{"dpi": 177.0, "threshold": 0.42}'""")
    ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=False)
    assert call_args.parameters == {"dpi": 177.0, "threshold": 0.42}
    ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=True)
    assert len(call_args.parameters) > 2


def test_falseness_basic(ocrd_parser, ocrd_validator):
    false_commands = [
        "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN -Z",
        "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN WRONG-TOKEN",
        "cis-ocropy-binarize -I OCR-D-IMG OCR-D-IMG2 -O OCR-D-BIN",
        "cis-ocropy-binarize -I OCR-D-IMG,OCR-D-IMG2 -O OCR-D-BIN",
        "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN OCR-D-BIN2",
        "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN,OCR-D-BIN2",
    ]
    with raises(ValueError):
        for command in false_commands:
            ocrd_parser.parse_arguments(command)


def test_falseness_with_params_separated(ocrd_parser, ocrd_validator):
    call_args: ProcessorCallArguments = ocrd_parser.parse_arguments(
        "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN -P dpi 177.0 -P non-existing-param 0.42")
    with raises(ValueError):
        ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=False)
    with raises(ValueError):
        ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=True)


def test_falseness_with_params_clustered(ocrd_parser, ocrd_validator):
    call_args: ProcessorCallArguments = ocrd_parser.parse_arguments(
        """cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN -p '{"dpi": 177.0, "non-existing-param": 0.42}'""")
    with raises(ValueError):
        ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=False)
    with raises(ValueError):
        ocrd_validator.validate_processor_params(processor_args=call_args, overwrite_with_defaults=True)
