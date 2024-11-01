from pytest import raises

def test_correctness(ocrd_validator):
    correct_lines = ["ocrd process"]
    for line in correct_lines:
        assert ocrd_validator.validate_ocrd_process_command(line=line)

def test_falseness(ocrd_validator):
    incorrect_lines = ["ocrd process \\", "process \\", "ocrd process \\ a", " ocrd process", "ocrd process "]
    with raises(ValueError):
        for line in incorrect_lines:
            assert ocrd_validator.validate_ocrd_process_command(line=line)
