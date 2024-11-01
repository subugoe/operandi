processor_command = "calamari-recognize -I OCR-D-IN1,OCR-D-IN2 -O OCR-D-OCR -P checkpoint_dir qurator-gt4histocr-1.0"
test_sample_lines = [
    f'"{processor_command}" \\',
    f'"{processor_command}"',
    f'    "{processor_command}"     \\',
    f'    "{processor_command}"    ',
]

processor_command2 = "calamari-recognize -I OCR-D-IN1,OCR-D-IN2 -O OCR-D-OCR -p '{'checkpoint_dir': 'qurator-gt4histocr-1.0'}'"
test_sample_lines2 = [
    f'"{processor_command2}" \\',
    f'"{processor_command2}"',
    f'    "{processor_command2}"     \\',
    f'    "{processor_command2}"    ',
]

def test_with_slash(ocrd_parser):
    purified_line = ocrd_parser.purify_line(test_sample_lines[0])
    assert processor_command == purified_line
    purified_line = ocrd_parser.purify_line(test_sample_lines2[0])
    assert processor_command2 == purified_line

def test_without_slash(ocrd_parser):
    purified_line = ocrd_parser.purify_line(test_sample_lines[1])
    assert processor_command == purified_line
    purified_line = ocrd_parser.purify_line(test_sample_lines2[1])
    assert processor_command2 == purified_line

def test_with_whitespaces_and_slash(ocrd_parser):
    purified_line = ocrd_parser.purify_line(test_sample_lines[2])
    assert processor_command == purified_line
    purified_line = ocrd_parser.purify_line(test_sample_lines2[2])
    assert processor_command2 == purified_line

def test_with_whitespaces_and_without_slash(ocrd_parser):
    purified_line = ocrd_parser.purify_line(test_sample_lines[3])
    assert processor_command == purified_line
    purified_line = ocrd_parser.purify_line(test_sample_lines2[3])
    assert processor_command2 == purified_line
