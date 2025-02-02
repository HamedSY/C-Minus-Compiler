generated_code = []
# we divided memory into 3 parts. (0,5000) (5000,10000) (10000,...)
global_section = 5000
stack_section = 10000
global_section_ptr = global_section


def variable_interpret(var, i, stay_with_address=False):
    assert var[1] not in ['#@', '@#']
    # if variable var is in the stack and we have its address based on stack frame, then we calculate its global address.
    if '$' in var[1]:
        generated_code.append(["ADD",
                               runtime_address_stack_frame[2],
                               '#{}'.format(var[2]),
                               reserved_global_vars[i][2]
                               ])
        # if we want to accsess the element indirectly, then we use @var as an address of our main variable.
        if '@' in var[1]:
            generated_code.append(["ASSIGN",
                                   '@{}'.format(reserved_global_vars[i][2]),
                                   reserved_global_vars[i][2]
                                   ])
        if stay_with_address is False:
            return '@{}'.format(reserved_global_vars[i][2])
        return reserved_global_vars[i][2]
    return var[1] + str(var[2])


def interpret_code(code):
    code = code.copy()
    gen_code = [code[0]]
    for i in range(1, len(code)):
        gen_code.append(variable_interpret(code[i], i - 1))
    generated_code.append(gen_code)


def get_new_global_address(sz=1):
    global global_section_ptr
    global_section_ptr += 4 * sz
    return global_section_ptr - 4 * sz


# return free global address to use it as a temp variable
def get_new_global_tmp():
    address = get_new_global_address()
    interpret_code([
        'ASSIGN',
        ['', '#', stack_section],
        ['', '', address]
    ])
    return ["", "", address]


runtime_address_stack_ptr = get_new_global_tmp()
runtime_address_stack_frame = get_new_global_tmp()
reserved_global_vars = [get_new_global_tmp() for i in range(4)]

generated_code.append(['JP'])
main_starter_jump = len(generated_code) - 1

stack = []
global_action_table = {}
local_action_table = {}
local_function_name = None
runtime_stack_ptr = 0
saved_stack_frame = None
repeat = []

function_call_args = []


def get_new_stack_address(sz=1):
    global runtime_stack_ptr
    assert runtime_stack_ptr is not None
    # interpret_code([
    #     'ADD',
    #     ['', '#', 4 * sz],
    #     runtime_address_stack_ptr,
    #     runtime_address_stack_ptr
    # ])
    runtime_stack_ptr += sz * 4
    return runtime_stack_ptr - 4 * sz


# not complete
# return the address of given variable
def get_var(line_n, pid):
    # if the given variable belongs to local variables, then return its address

    if pid in local_action_table:
        return local_action_table[pid]
    # if the given variable belongs to global variables, then return its address
    elif pid in global_action_table:
        return global_action_table[pid]
    # if there is not any variable with the given ID, then show semantic error
    else:
        scoping_error(line_n, pid)
        return [
            'NA', '', 0
        ]  # we return something meaningful enough to prevent errors ...


# returns a free cell in stack to use it as a temp variable
def get_new_stack_tmp():
    address = get_new_stack_address()
    return ["NA", "$", address]


# ['array', '$', 12]

def code_gen(routine_name, token, line_n):
    # print(routine_name, token, line_n)
    # generated_code.append(["++++++++++++++++++++++++", routine_name, token, line_n])
    global stack
    global global_action_table
    global local_action_table
    global local_function_name
    global runtime_stack_ptr
    global saved_stack_frame

    debug_mode = False
    debug_mode2 = False
    print(stack)
    # print(routine_name)
    # action symbol's subroutines
    if routine_name == 'type_specifier':
        stack.append(token)
    elif routine_name == 'put_id':
        if local_function_name is None:
            global_action_table[token] = list()
        else:
            local_action_table[token] = list()
        stack.append(token)
    elif routine_name == 'none_array_declaration':
        pid = stack.pop()
        tp = stack.pop()
        void_type_semantic_check(line_n, tp, pid)

        if pid in local_action_table:
            local_action_table[pid] = [tp, "$", get_new_stack_address()]
        else:
            global_action_table[pid] = [tp, "", get_new_global_address()]
    elif routine_name == 'array_declaration':
        pid = stack.pop()
        tp = stack.pop()
        void_type_semantic_check(line_n, tp, pid)

        if pid in local_action_table:
            address = get_new_stack_address(int(token))
            tmp = get_new_stack_tmp()
            generated_code.append([
                'ASSIGN',
                variable_interpret(['', '$', address], 1, stay_with_address=True),
                variable_interpret(tmp, 2)
            ])
            local_action_table[pid] = ["array", "$", tmp[2]]
        else:
            address = get_new_global_address(int(token))
            global_action_table[pid] = ["array", "#", address]
    # declare function and add its record
    elif routine_name == 'fun_declaration':
        fname = stack.pop()
        return_tp = stack.pop()

        global_action_table[fname] = {'name': fname, 'return_type': return_tp, 'param': [],
                                      'address': len(generated_code)}
        local_function_name = fname
        runtime_stack_ptr = 8  # first 8 bytes are reserved for return value and stack
        if debug_mode:
            generated_code.append(['PRINT', 5000])
            generated_code.append(['PRINT', 5004])
    # reset all ther variables and arrays
    elif routine_name == 'fun_declaration_end':
        code_gen('return_void', None, line_n)
        local_action_table = {}
        local_function_name = None
        runtime_stack_ptr = 0
    elif routine_name == 'param_type_array':
        pid = stack.pop()
        tp = stack.pop()
        void_type_semantic_check(line_n, tp, pid)

        local_action_table[pid] = ["array", "$", runtime_stack_ptr]
        runtime_stack_ptr += 4
        global_action_table[local_function_name]['param'].append('array')
    elif routine_name == 'param_type_n_array':
        pid = stack.pop()
        tp = stack.pop()
        void_type_semantic_check(line_n, tp, pid)

        local_action_table[pid] = [tp, "$", runtime_stack_ptr]
        runtime_stack_ptr += 4
        global_action_table[local_function_name]['param'].append(tp)
    elif routine_name == 'main_starter':
        generated_code[main_starter_jump].append(len(generated_code))
        code_gen('pid', 'main', -2)
        code_gen('start_args', None, -2)
        code_gen('call_function', None, -2)
    elif routine_name == "save_stack_frame":
        saved_stack_frame = runtime_stack_ptr
        interpret_code(["ASSIGN",
                        runtime_address_stack_frame,
                        ['', '@', runtime_address_stack_ptr[2]]])
        interpret_code(["ASSIGN", runtime_address_stack_ptr, runtime_address_stack_frame])
        interpret_code(["SUB",
                        runtime_address_stack_frame,
                        ['', '#', runtime_stack_ptr],
                        runtime_address_stack_frame])
        get_new_stack_tmp()
    # apply the operation, which has pushed into stack before, to operands
    elif routine_name == 'do_operation':
        tmp = get_new_stack_tmp()
        # print(stack[-3:])
        res = type_mismatch_check(stack[-1][0], stack[-3][0], line_n)
        interpret_code([
            stack[-2],
            stack[-3],
            stack[-1],
            tmp
        ])
        tmp[0] = res
        stack.pop()
        stack.pop()
        stack.pop()
        stack.append(tmp)
    # push the operation which should be applied later into the stack
    elif routine_name == 'save_operation':
        if token == '+':
            stack.append('ADD')
        elif token == '-':
            stack.append('SUB')
        elif token == '*':
            stack.append('MULT')
        elif token == '/':
            stack.append('DIV')
        elif token == '==':
            stack.append('EQ')
        elif token == '<':
            stack.append('LT')
    # push ID token and its line into stack
    elif routine_name == 'pid':
        stack.append(get_var(line_n, token))
    elif routine_name == 'array_index':
        tmp = get_new_stack_tmp()
        interpret_code([
            'ADD',
            stack[-1],
            stack[-2],
            tmp
        ])
        # tmp2 = get_new_stack_tmp()
        # tmp[1] += '@'
        # interpret_code([
        #     'ASSIGN',
        #     tmp,
        #     tmp2
        # ])
        stack.pop()
        stack.pop()
        # stack.append(tmp2)
        stack.append(['int', '@$', tmp[2]])
    elif routine_name == 'assign':
        interpret_code([
            'ASSIGN',
            stack[-1],
            stack[-2]
        ])
        stack.pop()
    # push NUM into stack
    elif routine_name == 'push':
        stack.append(['int', '#', str(token)])
    elif routine_name == 'start_args':
        function_call_args.append([])
    # add top element of stack (argument of called function) to function's arguments array
    elif routine_name == 'fill_record':
        function_call_args[-1].append(stack.pop())
    # pop called function's arguments and then check types of arguments and parameters.
    # Consider 2 free memory cell for return value and return address.
    # Assign each argument to its corresponding parameter.
    elif routine_name == 'call_function':
        f = stack.pop()
        # print(f)
        args = function_call_args.pop()
        args_check(f['param'], args, f['name'], line_n)

        return_value = get_new_stack_tmp()  # stack_frame

        tmp2 = runtime_stack_ptr

        return_address = get_new_stack_tmp()
        for arg in args:
            tmp = get_new_stack_tmp()
            # print("-----------", arg, tmp)
            interpret_code([
                'ASSIGN',
                arg,
                tmp
            ])
        interpret_code([
            'ADD',
            ['', '#', runtime_stack_ptr],
            runtime_address_stack_frame,
            runtime_address_stack_ptr
        ])
        interpret_code([
            'ASSIGN',
            ['', '', 0],
            return_address
        ])
        generated_code[-1][1] = '#{}'.format(len(generated_code) + 1)
        interpret_code([
            'JP',
            ['', '', f['address']]
        ])
        return_value[0] = f['return_type']
        stack.append(return_value)
        runtime_stack_ptr = tmp2
    # adjust stack frame address and jump to where we called the function
    elif routine_name == 'return_void':
        interpret_code([
            'ADD',
            runtime_address_stack_frame,
            ['', '#', 4],
            runtime_address_stack_ptr
        ])
        interpret_code([
            'ASSIGN',
            ['', '$', 4],
            reserved_global_vars[3]
        ])
        interpret_code(["ASSIGN",
                        ['', '$', saved_stack_frame],
                        runtime_address_stack_frame
                        ])
        if debug_mode:
            generated_code.append(['PRINT', 5000])
            generated_code.append(['PRINT', 5004])
        interpret_code([
            'JP',
            ['', '@', reserved_global_vars[3][2]]
        ])
    # adjust stack frame and assign return value(which is in the cell 4 of stack) to the global var which has been considered for the return value
    elif routine_name == 'return_value':
        interpret_code([
            'ASSIGN',
            stack.pop(),
            ['', '$', 0]
        ])
        interpret_code([
            'ADD',
            runtime_address_stack_frame,
            ['', '#', 4],
            runtime_address_stack_ptr
        ])
        interpret_code([
            'ASSIGN',
            ['', '$', 4],
            reserved_global_vars[3]
        ])
        interpret_code(["ASSIGN",
                        ['', '$', saved_stack_frame],
                        runtime_address_stack_frame
                        ])
        if debug_mode:
            generated_code.append(['PRINT', 5000])
            generated_code.append(['PRINT', 5004])
        interpret_code([
            'JP',
            ['', '@', reserved_global_vars[3][2]]
        ])
    elif routine_name == 'pop':
        stack.pop()
    # if we have reached a break out of repeat block then detect it as a semantic error.otherwise, add it to the current repeat block array
    elif routine_name == 'save_break':
        interpret_code([
            "JP",
            ['', '', 0],
        ])
        if len(repeat) == 0:
            break_semantic_error(line_n)
        else:
            repeat[-1].append(len(generated_code) - 1)
    # add JPF command and fill it with appropriate addrees later
    elif routine_name == 'save':
        interpret_code([
            "JPF",
            stack.pop(),  # stack(top)
            ['', '', 0],
        ])
        stack.append(['', '', len(generated_code) - 1])
    # determine jump address for JPF command
    elif routine_name == 'jpf':
        generated_code[stack.pop()[2]][2] = (len(generated_code))
    # determine jump address for JPF command and save a block for JP command to fill later
    elif routine_name == 'jpfw':
        generated_code[stack.pop()[2]][2] = (len(generated_code) + 1)

    elif routine_name == 'jpf_save':
        generated_code[stack.pop()[2]][2] = len(generated_code) + 1  # i+1
        interpret_code([
            "JP",
            ['', '', 0],
        ])
        stack.append(['', '', len(generated_code) - 1])
    # determine jump address for JP command
    elif routine_name == 'jp':
        generated_code[stack.pop()[2]][1] = len(generated_code)
    elif routine_name == 'label':
        stack.append(['', '', len(generated_code)])
        repeat.append([])
    elif routine_name == 'while':
        print(stack)
        interpret_code([
            "JP",
            stack.pop(),
        ])
        for br in repeat[-1]:
            generated_code[br][1] = len(generated_code)


    else:
        raise Exception("no such action symbol in code_gen()!")

    if debug_mode2:
        generated_code.append(["-------------------------{}".format(runtime_stack_ptr), routine_name, token, line_n])


def flush_outputs():
    semantic_errors_list = get_errors_list()

    semantic_errors_file = open("semantic_errors.txt", 'w')
    output_file = open("output.txt", 'w')

    if len(semantic_errors_list) > 0:
        output_file.write('The code has not been generated.\n')
        for err in semantic_errors_list:
            semantic_errors_file.write(err + '\n')
    else:
        semantic_errors_file.write('The input program is semantically correct.\n')
        i = 0
        for code in generated_code:
            while len(code) < 4:
                code.append('')
            output_file.write("{}\t({}, {}, {}, {})\n".format(i, code[0], code[1], code[2], code[3]))
            if code[0][0] not in '-+':
                i += 1

    semantic_errors_file.close()
    output_file.close()


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
