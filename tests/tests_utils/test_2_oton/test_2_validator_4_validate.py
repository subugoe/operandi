from pytest import raises
from tests.assets.oton.constants import (
    IN_TXT_WF1, IN_TXT_WF2, IN_TXT_WF3, IN_TXT_WF4, INVALID_WF1, INVALID_WF2, INVALID_WF3)


def test_correctness_wf1(ocrd_validator):
    ocrd_validator.validate(input_file=IN_TXT_WF1)

def test_correctness_wf2(ocrd_validator):
    ocrd_validator.validate(input_file=IN_TXT_WF2)

def test_correctness_wf3(ocrd_validator):
    ocrd_validator.validate(input_file=IN_TXT_WF3)

def test_correctness_wf4(ocrd_validator):
    ocrd_validator.validate(input_file=IN_TXT_WF4)

def test_falseness_invalid_wf1(ocrd_validator):
    with raises(ValueError):
        ocrd_validator.validate(input_file=INVALID_WF1)

def test_falseness_invalid_wf2(ocrd_validator):
    with raises(ValueError):
        ocrd_validator.validate(input_file=INVALID_WF2)

def test_falseness_invalid_wf3(ocrd_validator):
    with raises(IndexError) or raises(ValueError):
        ocrd_validator.validate(input_file=INVALID_WF3)
