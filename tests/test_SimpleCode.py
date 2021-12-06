# Testing the functions of the simple calculator

import pytest
import sys

# Set the proper path and import the functions that will be tested
sys.path.append('./src')
from SimpleCode import addFunc, subFunc, mulFunc, divFunc

# Test addFunc
def test_addFunc_1():
	num1 = 10
	num2 = 4
	result = addFunc(num1, num2)
	expected = num1+num2
	assert result == expected

def test_addFunc_2():
	num1 = 10
	num2 = 4
	# intentionally produce wrong result
	result = addFunc(num1, num2) + 1
	expected = num1+num2

	# assert that the wrong result is different from the expected
	assert result != expected

# Test subFunc		
def test_subFunc_1():
	num1 = 10
	num2 = 4
	result = subFunc(num1, num2)
	expected = num1-num2
	assert result == expected

# Test mulFunc
def test_mulFunc_1():
	num1 = 10
	num2 = 4
	result = mulFunc(num1, num2)
	expected = num1*num2
	assert result == expected

# Test divFunc
def test_divFunc_1():
	num1 = 10
	num2 = 4
	result = divFunc(num1, num2)
	expected = num1/num2
	assert result == expected

def test_divFunc_2():
	num1 = 10
	num2 = 0
	result = divFunc(num1, num2)
	if num2 != 0:
		expected = num1/num2
	else:
		expected = None
	assert result == expected