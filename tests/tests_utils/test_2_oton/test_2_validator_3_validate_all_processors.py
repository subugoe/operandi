from pytest import raises
from operandi_utils.oton import ProcessorCallArguments


# False order of chaining previous output to next input file groups
false_processors_call_args1 = [
    ProcessorCallArguments("cis-ocropy-binarize", "OCR-D-IMG", "OCR-D-BIN", {"dpi": 241.0}),
    ProcessorCallArguments("anybaseocr-crop", "NON-EXISTING", "OCR-D-CROP"),
    ProcessorCallArguments("skimage-binarize", "OCR-D-CROP", "OCR-D-BIN2")
]


def test_correctness_basic(ocrd_validator):
    # Correct order of chaining previous output to next input file groups
    correct_processors_call_args = [
        ProcessorCallArguments("cis-ocropy-binarize", "OCR-D-IMG", "OCR-D-BIN", {"dpi": 241.0}),
        ProcessorCallArguments("anybaseocr-crop", "OCR-D-BIN", "OCR-D-CROP"),
        ProcessorCallArguments("skimage-binarize", "OCR-D-CROP", "OCR-D-BIN2")
    ]
    ocrd_validator.validate_all_processors(processors=correct_processors_call_args)


def test_correctness_with_gt_and_ocr(ocrd_validator):
    # Correct order of chaining previous output to next input file groups with GT data file groups
    correct_processors_call_args = [
        ProcessorCallArguments("dinglehopper", "OCR-D-GT-SEG-BLOCK,OCR-D-OCR", "OCR-D-EVAL-SEG-BLOCK"),
        ProcessorCallArguments("dinglehopper", "OCR-D-GT-SEG-LINE,OCR-D-OCR", "OCR-D-EVAL-SEG-LINE"),
        ProcessorCallArguments("dinglehopper", "OCR-D-GT-SEG-PAGE,OCR-D-OCR", "OCR-D-EVAL-SEG-PAGE")
    ]
    ocrd_validator.validate_all_processors(processors=correct_processors_call_args)


def test_falseness_basic(ocrd_validator):
    # False order of chaining previous output to next input file groups
    false_processors_call_args = [
        ProcessorCallArguments("cis-ocropy-binarize", "OCR-D-IMG", "OCR-D-BIN", {"dpi": 241.0}),
        ProcessorCallArguments("anybaseocr-crop", "OCR-D-CROP", "OCR-D-BIN2"),
        ProcessorCallArguments("skimage-binarize", "OCR-D-BIN2", "OCR-D-CROP")
    ]
    with raises(ValueError):
        ocrd_validator.validate_all_processors(processors=false_processors_call_args)


def test_falseness_non_existing_file_group(ocrd_validator):
    # False order of chaining previous output to next input file groups
    false_processors_call_args = [
        ProcessorCallArguments("cis-ocropy-binarize", "OCR-D-IMG", "OCR-D-BIN", {"dpi": 241.0}),
        ProcessorCallArguments("anybaseocr-crop", "NON-EXISTING", "OCR-D-CROP"),
        ProcessorCallArguments("skimage-binarize", "OCR-D-CROP", "OCR-D-BIN2")
    ]
    with raises(ValueError):
        ocrd_validator.validate_all_processors(processors=false_processors_call_args)
