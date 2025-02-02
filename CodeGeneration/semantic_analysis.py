semantic_errors_list = []


def get_errors_list():
    return semantic_errors_list


# return a semantic error when we reached a "break" outside a repeat block
def break_semantic_error(linen):
    semantic_errors_list.append(
        "#{} : Semantic Error! No 'repeat ... until' found for 'break'.".format(linen)
    )


def void_type_semantic_check(linen, tp, pid):
    global semantic_errors_list
    if tp == 'void':
        semantic_errors_list.append(
            "#{} : Semantic Error! Illegal type of void for '{}'.".format(linen, pid)
        )


# return a semantic error when we reached an undefined variable
def scoping_error(linen, pid):
    global semantic_errors_list
    semantic_errors_list.append(
        "#{} : Semantic Error! '{}' is not defined.".format(linen, pid)
    )


# return a semantic error when there is type mismatch between operands
def type_mismatch_check(first_arg, second_arg, line_n):
    if first_arg != 'NA' and second_arg != 'NA' and first_arg != second_arg:
        semantic_errors_list.append(
            "#{} : Semantic Error! Type mismatch in operands, Got {} instead of {}.".format(line_n, first_arg,
                                                                                            second_arg)
        )
        return 'NA'
    return first_arg


# return a semantic error when there is a type mismatch between parameters and arguments of a function
def args_check(expected_args, input_args, fname, line_n):
    if len(expected_args) != len(input_args):
        semantic_errors_list.append(
            "#{} : Semantic Error! Mismatch in numbers of arguments of '{}'.".format(line_n, fname)
        )
    for i, (a, b) in enumerate(zip(expected_args, input_args)):
        b = b[0]
        if b != 'NA' and a != b:
            semantic_errors_list.append(
                "#{} : Semantic Error! Mismatch in type of argument {} of '{}'. Expected '{}' but got '{}' instead.".format(
                    line_n, i + 1, fname, a, b)
            )
