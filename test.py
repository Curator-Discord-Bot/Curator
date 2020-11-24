from math import sqrt

binaryops = '+-*/^'
unaryops = '#%!'
ops = binaryops + unaryops + 'q'


def main():
    total = run_calculator()


def run_calculator():
    total = 0
    while True:  # true while loop vil forsætte uendeligt, indtil der kommer et break statement
        optr, oprnd = scan_data()
        if optr == 'q':
            break
        total = do_next_op(optr, oprnd, total)
        print(f'Result so far is: {total}')
    print(f'Final result is: {total}')
    return total


def scan_data():
    while True:
        optr = input('Enter an operator: ')

        if len(optr) != 1 and not optr in ops:
            print('Error: The operator must be one of: \"' + ops + '\".')
        else:
            break

    if optr in binaryops:
        while True:
            oprnd = input('Enter an operand: ')

            try:  # prøver følgende:
                return (optr, float(oprnd))
            except ValueError:  # ellers hvis der kommer valueerror, så gør den det her.
                print('Error: Operand must be a number.')
    else:
        return (optr, None)  # returner optr, men ingen operand. Returnes som en tuple, der indeholder to værdier


def do_next_op(optr, oprnd, total):
    if optr in '+-*/':
        return eval(f'{total}{optr}{oprnd}')  # eval regner det ud som om man havde skrevet det: f.eks. 5*3
    # elif betyder else if
    elif optr == '^':
        return total ** oprnd
    elif optr == '#':
        return sqrt(total)
    elif optr == '%':
        return -total
    elif optr == '!':
        return total / 1
    print('Error: Invalid input')


# python har ikke main, og kører i stedet som et script fra top til bund. Så der er ikke nogen desideret main, og vi skal selv kører den.
main()
