# Simple calculator

def addFunc(num1, num2):
    return num1+num2

def subFunc(num1, num2):
    return num1-num2

def mulFunc(num1, num2):
    return num1*num2

def divFunc(num1, num2):
    if num2 != 0:
        return num1/num2
    else:
        print("The second number is 0. Division by 0 is not possible!")
        return None

if __name__ == "__main__":

    num1 = int(input("Enter the first integer number: "))
    print("The first number is:", num1)

    num2 = int(input("Enter the second integer number: "))
    print("The second number is:", num2)

    print("The add of the two numbers is:", addFunc(num1, num2))
    print("The sub of the two numbers is:", subFunc(num1, num2))
    print("The mul of the two numbers is:", mulFunc(num1, num2))
    print("The div of the two numbers is:", divFunc(num1, num2))