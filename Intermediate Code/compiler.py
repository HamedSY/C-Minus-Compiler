# Add these global variables at the top of compiler.py
current_scope = 0
temp_counter = 0
label_counter = 0
semantic_stack = []
symbol_table = []
output_code = []
memory_address = 0

# Scanner

# Global variables to store DFA information
num_states = 15
transitions = [[] for _ in range(num_states)]
accept_states = [False] * num_states

# accepting states
accept_states[1] = True  # Symbol
accept_states[2] = True  # Symbol
accept_states[6] = True  # Symbol
accept_states[7] = True  # Number (NUM)
accept_states[9] = True  # Comment
accept_states[13] = True  # ID/Keyword
accept_states[12] = True  # Whitespace (to be ignored)

# Character groups
digit = "0123456789"
sym = "[](){}+-*<;:,="
whitespace = " \n\f\r\v\t"
English_alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Define DFA transitions manually
transitions[0].append(("*", True, 14))
transitions[14].append((sym + digit + whitespace + English_alphabet, False, 1))
transitions[0].append(("[](){}+-<;:,", True, 1))
transitions[0].append(("=", True, 3))
transitions[3].append(("=", True, 1))  # '==' symbol
transitions[3].append(("/\0" + sym + digit + whitespace + English_alphabet, False, 2))  # '=' symbol
transitions[0].append((digit, True, 4))  # Start of a number
transitions[4].append((digit, True, 4))  # Continue reading digits
transitions[4].append((sym + whitespace + "/\0", False, 7))  # Finalize the number
transitions[0].append(("/", True, 6))  # Start of comment
transitions[6].append(("*", True, 5))  # Block comment start '/*'
transitions[5].append(('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()+,-./:;<=>?@['
                       '\\]^_`{|}~ \n\t\r\x0b\x0c', True, 5))  # Inside comment
transitions[6].append(("/", True, 10))  # Line comment start '//'
transitions[10].append(('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@['
                        '\\]^_`{|}~ \t\r\x0b\x0c', True, 10))  # Inside line comment
transitions[10].append(("\n\0", True, 9))  # End of line comment
transitions[5].append(("*", True, 8))  # Block comment end '*/'
transitions[8].append(("*", True, 8))  # More stars in block comment
transitions[8].append(("[](){}+-<;:,=" + digit + whitespace + English_alphabet, True, 5))  # Inside comment
transitions[8].append(("/", True, 9))  # End of block comment
transitions[0].append((English_alphabet, True, 11))  # Start of identifier
transitions[11].append((digit + English_alphabet, True, 11))  # Continue reading identifier
transitions[11].append(("/\0" + sym + whitespace, False, 13))  # Finalize identifier
transitions[0].append((whitespace, True, 12))  # Whitespace


def get_next_state(current_state, character):
    for (characters, included, next_state) in transitions[current_state]:
        if character in characters:
            return next_state, included
    return None, None


KEYWORDS = {"break", "else", "if", "endif", "int", "while", "return", "void"}


class Scanner:
    def __init__(self, file_name):
        self.index = 0
        self.file = open(file_name, 'r')
        self.input_text = self.file.read()
        self.current_line = 1

    def get_next_token(self):
        current_state = 0
        lexeme = ""

        while self.index < len(self.input_text):
            char = self.input_text[self.index]
            next_state, is_included = get_next_state(current_state, char)

            if next_state is None:
                error_found = False
                if accept_states[current_state]:
                    if current_state == 1 or current_state == 2 or current_state == 6:  # Symbol found
                        return lexeme, "SYMBOL", lexeme, self.current_line
                    elif current_state == 7:  # Number found
                        return "NUM", "NUM", lexeme, self.current_line
                    elif current_state == 13:  # ID or keyword found
                        if lexeme in KEYWORDS:
                            return lexeme, "KEYWORD", lexeme, self.current_line
                        else:
                            return "ID", "ID", lexeme, self.current_line
                    elif current_state == 12:  # Whitespace found
                        pass  # Ignore
                else:
                    error_found = True

                # Reset for the next token
                lexeme = ""
                current_state = 0
                if char in whitespace or error_found:
                    self.index += 1
                    if char == '\n':
                        self.current_line += 1
                continue

            if is_included:
                lexeme += char
                self.index += 1
            current_state = next_state

            if lexeme == '\n':
                self.current_line += 1

        self.file.close()
        return "$", "EOF", "$", self.current_line


"""## Dicts"""
# Here are the dictionaries we have extracted from the site shared on the homework's document.

first_sets = {
    'Program': ['int', 'void', 'ε'],
    'DeclarationList': ['int', 'void', 'ε'],
    'Declaration': ['int', 'void'],
    'DeclarationInitial': ['int', 'void'],
    'DeclarationPrime': [';', '[', '('],
    'VarDeclarationPrime': [';', '['],
    'FunDeclarationPrime': ['('],
    'TypeSpecifier': ['int', 'void'],
    'Params': ['int', 'void'],
    'ParamList': [',', 'ε'],
    'Param': ['int', 'void'],
    'ParamPrime': ['[', 'ε'],
    'CompoundStmt': ['{'],
    'StatementList': ['ID', ';', 'NUM', '(', '{', 'break', 'if', 'while', 'return', '+', '-', 'ε'],
    'Statement': ['ID', ';', 'NUM', '(', '{', 'break', 'if', 'while', 'return', '+', '-'],
    'ExpressionStmt': ['ID', ';', 'NUM', '(', 'break', '+', '-'],
    'SelectionStmt': ['if'],
    'ElseStmt': ['endif', 'else'],
    'IterationStmt': ['while'],
    'ReturnStmt': ['return'],
    'ReturnStmtPrime': ['ID', ';', 'NUM', '(', '+', '-'],
    'Expression': ['ID', 'NUM', '(', '+', '-'],
    'B': ['[', '(', '=', '<', '==', '+', '-', '*', '/', 'ε'],
    'H': ['=', '<', '==', '+', '-', '*', '/', 'ε'],
    'SimpleExpressionZegond': ['NUM', '(', '+', '-'],
    'SimpleExpressionPrime': ['(', '<', '==', '+', '-', '*', '/', 'ε'],
    'C': ['<', '==', 'ε'],
    'Relop': ['<', '=='],
    'AdditiveExpression': ['ID', 'NUM', '(', '+', '-'],
    'AdditiveExpressionPrime': ['(', '+', '-', '*', '/', 'ε'],
    'AdditiveExpressionZegond': ['NUM', '(', '+', '-'],
    'D': ['+', '-', 'ε'],
    'Addop': ['+', '-'],
    'Term': ['ID', 'NUM', '(', '+', '-'],
    'TermPrime': ['(', '*', '/', 'ε'],
    'TermZegond': ['NUM', '(', '+', '-'],
    'G': ['*', '/', 'ε'],
    'Mulop': ['*', '/'],
    'SignedFactor': ['ID', 'NUM', '(', '+', '-'],
    'SignedFactorPrime': ['(', 'ε'],
    'SignedFactorZegond': ['NUM', '(', '+', '-'],
    'Factor': ['ID', 'NUM', '('],
    'VarCallPrime': ['[', '(', 'ε'],
    'VarPrime': ['[', 'ε'],
    'FactorPrime': ['(', 'ε'],
    'FactorZegond': ['NUM', '('],
    'Args': ['ID', 'NUM', '(', '+', '-', 'ε'],
    'ArgList': ['ID', 'NUM', '(', '+', '-'],
    'ArgListPrime': [',', 'ε']
}

follow_sets = {
    'Program': ['$'],
    'DeclarationList': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'while', 'return', '+', '-', '$'],
    'Declaration': ['ID', ';', 'NUM', '(', 'int', 'void', '{', '}', 'break', 'if', 'while', 'return', '+', '-', '$'],
    'DeclarationInitial': [';', '[', '(', ')', ','],
    'DeclarationPrime': ['ID', ';', 'NUM', '(', 'int', 'void', '{', '}', 'break', 'if', 'while', 'return', '+', '-',
                         '$'],
    'VarDeclarationPrime': ['ID', ';', 'NUM', '(', 'int', 'void', '{', '}', 'break', 'if', 'while', 'return', '+', '-',
                            '$'],
    'FunDeclarationPrime': ['ID', ';', 'NUM', '(', 'int', 'void', '{', '}', 'break', 'if', 'while', 'return', '+', '-',
                            '$'],
    'TypeSpecifier': ['ID'],
    'Params': [')'],
    'ParamList': [')'],
    'Param': [')', ','],
    'ParamPrime': [')', ','],
    'CompoundStmt': ['ID', ';', 'NUM', '(', 'int', 'void', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return',
                     '+', '-', '$'],
    'StatementList': ['}'],
    'Statement': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return', '+', '-'],
    'ExpressionStmt': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return', '+', '-'],
    'SelectionStmt': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return', '+', '-'],
    'ElseStmt': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return', '+', '-'],
    'IterationStmt': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return', '+', '-'],
    'ReturnStmt': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return', '+', '-'],
    'ReturnStmtPrime': ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'endif', 'else', 'while', 'return', '+', '-'],
    'Expression': [';', ']', ')', ','],
    'B': [';', ']', ')', ','],
    'H': [';', ']', ')', ','],
    'SimpleExpressionZegond': [';', ']', ')', ','],
    'SimpleExpressionPrime': [';', ']', ')', ','],
    'C': [';', ']', ')', ','],
    'Relop': ['ID', 'NUM', '(', '+', '-'],
    'AdditiveExpression': [';', ']', ')', ','],
    'AdditiveExpressionPrime': [';', ']', ')', ',', '<', '=='],
    'AdditiveExpressionZegond': [';', ']', ')', ',', '<', '=='],
    'D': [';', ']', ')', ',', '<', '=='],
    'Addop': ['ID', 'NUM', '(', '+', '-'],
    'Term': [';', ']', ')', ',', '<', '==', '+', '-'],
    'TermPrime': [';', ']', ')', ',', '<', '==', '+', '-'],
    'TermZegond': [';', ']', ')', ',', '<', '==', '+', '-'],
    'G': [';', ']', ')', ',', '<', '==', '+', '-'],
    'Mulop': ['ID', 'NUM', '(', '+', '-'],
    'SignedFactor': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'SignedFactorPrime': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'SignedFactorZegond': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'Factor': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'VarCallPrime': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'VarPrime': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'FactorPrime': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'FactorZegond': [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    'Args': [')'],
    'ArgList': [')'],
    'ArgListPrime': [')']
}

predict_sets = {
    1: ['int', 'void', '$'],
    2: ['int', 'void'],
    3: ['ID', ';', 'NUM', '(', '{', '}', 'break', 'if', 'while', 'return', '+', '-', '$'],
    4: ['int', 'void'],
    5: ['int', 'void'],
    6: ['('],
    7: [';', '['],
    8: [';'],
    9: ['['],
    10: ['('],
    11: ['int'],
    12: ['void'],
    13: ['int'],
    14: ['void'],
    15: [','],
    16: [')'],
    17: ['int', 'void'],
    18: ['['],
    19: [')', ','],
    20: ['{'],
    21: ['ID', ';', 'NUM', '(', '{', 'break', 'if', 'while', 'return', '+', '-'],
    22: ['}'],
    23: ['ID', ';', 'NUM', '(', 'break', '+', '-'],
    24: ['{'],
    25: ['if'],
    26: ['while'],
    27: ['return'],
    28: ['ID', 'NUM', '(', '+', '-'],
    29: ['break'],
    30: [';'],
    31: ['if'],
    32: ['endif'],
    33: ['else'],
    34: ['while'],
    35: ['return'],
    36: [';'],
    37: ['ID', 'NUM', '(', '+', '-'],
    38: ['NUM', '(', '+', '-'],
    39: ['ID'],
    40: ['='],
    41: ['['],
    42: [';', ']', '(', ')', ',', '<', '==', '+', '-', '*', '/'],
    43: ['='],
    44: [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    45: ['NUM', '(', '+', '-'],
    46: [';', ']', '(', ')', ',', '<', '==', '+', '-', '*', '/'],
    47: ['<', '=='],
    48: [';', ']', ')', ','],
    49: ['<'],
    50: ['=='],
    51: ['ID', 'NUM', '(', '+', '-'],
    52: [';', ']', '(', ')', ',', '<', '==', '+', '-', '*', '/'],
    53: ['NUM', '(', '+', '-'],
    54: ['+', '-'],
    55: [';', ']', ')', ',', '<', '=='],
    56: ['+'],
    57: ['-'],
    58: ['ID', 'NUM', '(', '+', '-'],
    59: [';', ']', '(', ')', ',', '<', '==', '+', '-', '*', '/'],
    60: ['NUM', '(', '+', '-'],
    61: ['*', '/'],
    62: [';', ']', ')', ',', '<', '==', '+', '-'],
    63: ['*'],
    64: ['/'],
    65: ['+'],
    66: ['-'],
    67: ['ID', 'NUM', '('],
    68: [';', ']', '(', ')', ',', '<', '==', '+', '-', '*', '/'],
    69: ['+'],
    70: ['-'],
    71: ['NUM', '('],
    72: ['('],
    73: ['ID'],
    74: ['NUM'],
    75: ['('],
    76: [';', '[', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    77: ['['],
    78: [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    79: ['('],
    80: [';', ']', ')', ',', '<', '==', '+', '-', '*', '/'],
    81: ['('],
    82: ['NUM'],
    83: ['ID', 'NUM', '(', '+', '-'],
    84: [')'],
    85: ['ID', 'NUM', '(', '+', '-'],
    86: [','],
    87: [')']
}

"""## Parser"""

from anytree import RenderTree, Node

grammar = [
    {"Program": ["DeclarationList", "#program_end"]},
    {"DeclarationList": ["Declaration", "DeclarationList"]},
    {"DeclarationList": []},
    {"Declaration": ["DeclarationInitial", "DeclarationPrime"]},
    {"DeclarationInitial": ["TypeSpecifier", "ID", "#declare_id"]},
    {"DeclarationPrime": ["FunDeclarationPrime"]},
    {"DeclarationPrime": ["VarDeclarationPrime"]},
    {"VarDeclarationPrime": [";", "#var_decl_simple"]},
    {"VarDeclarationPrime": ["[", "NUM", "]", ";", "#var_decl_array"]},
    {"FunDeclarationPrime": ["(", "Params", ")", "#func_begin", "CompoundStmt", "#func_end"]},
    {"TypeSpecifier": ["int"]},
    {"TypeSpecifier": ["void"]},
    {"Params": ["int", "ID", "#param_int", "ParamPrime", "ParamList"]},
    {"Params": ["void", "#param_void"]},
    {"ParamList": [",", "Param", "ParamList"]},
    {"ParamList": []},
    {"Param": ["DeclarationInitial", "ParamPrime"]},
    {"ParamPrime": ["[", "]", "#param_array"]},
    {"ParamPrime": []},
    {"CompoundStmt": ["{", "#scope_begin", "DeclarationList", "StatementList", "}", "#scope_end"]},
    {"StatementList": ["Statement", "StatementList"]},
    {"StatementList": []},
    {"Statement": ["ExpressionStmt"]},
    {"Statement": ["CompoundStmt"]},
    {"Statement": ["SelectionStmt"]},
    {"Statement": ["IterationStmt"]},
    {"Statement": ["ReturnStmt"]},
    {"ExpressionStmt": ["Expression", ";", "#expr_end"]},
    {"ExpressionStmt": ["break", ";", "#break_stmt"]},
    {"ExpressionStmt": [";"]},
    {"SelectionStmt": ["if", "(", "Expression", ")", "#if_start", "Statement", "ElseStmt", "#if_end"]},
    {"ElseStmt": ["endif"]},
    {"ElseStmt": ["else", "#else_jump", "Statement", "endif"]},
    {"IterationStmt": ["while", "#while_start", "(", "Expression", ")", "#while_cond", "Statement", "#while_end"]},
    {"ReturnStmt": ["return", "ReturnStmtPrime"]},
    {"ReturnStmtPrime": [";", "#return_void"]},
    {"ReturnStmtPrime": ["Expression", ";", "#return_value"]},
    {"Expression": ["SimpleExpressionZegond", "#expr_eval"]},
    {"Expression": ["ID", "B", "#id_expr"]},
    {"B": ["=", "Expression", "#assign"]},
    {"B": ["[", "Expression", "]", "H", "#array_access"]},
    {"B": ["SimpleExpressionPrime", "#expr_eval"]},
    {"H": ["=", "Expression", "#assign"]},
    {"H": ["G", "D", "C", "#expr_eval"]},
    {"SimpleExpressionZegond": ["AdditiveExpressionZegond", "C", "#expr_eval"]},
    {"SimpleExpressionPrime": ["AdditiveExpressionPrime", "C", "#expr_eval"]},
    {"C": ["Relop", "AdditiveExpression", "#relop"]},
    {"C": []},
    {"Relop": ["<", "#set_lt"]},
    {"Relop": ["==", "#set_eq"]},
    {"AdditiveExpression": ["Term", "D", "#add_sub"]},
    {"AdditiveExpressionPrime": ["TermPrime", "D", "#add_sub"]},
    {"AdditiveExpressionZegond": ["TermZegond", "D", "#add_sub"]},
    {"D": ["Addop", "Term", "D", "#add_sub"]},
    {"D": []},
    {"Addop": ["+", "#set_add"]},
    {"Addop": ["-", "#set_sub"]},
    {"Term": ["SignedFactor", "G", "#mult_div"]},
    {"TermPrime": ["SignedFactorPrime", "G", "#mult_div"]},
    {"TermZegond": ["SignedFactorZegond", "G", "#mult_div"]},
    {"G": ["Mulop", "SignedFactor", "G", "#mult_div"]},
    {"G": []},
    {"Mulop": ["*", "#set_mult"]},
    {"Mulop": ["/", "#set_div"]},
    {"SignedFactor": ["+", "Factor", "#signed_factor"]},
    {"SignedFactor": ["-", "Factor", "#signed_factor"]},
    {"SignedFactor": ["Factor"]},
    {"SignedFactorPrime": ["FactorPrime"]},
    {"SignedFactorZegond": ["+", "Factor", "#signed_factor"]},
    {"SignedFactorZegond": ["-", "Factor", "#signed_factor"]},
    {"SignedFactorZegond": ["FactorZegond"]},
    {"Factor": ["(", "Expression", ")", "#paren_expr"]},
    {"Factor": ["ID", "VarCallPrime", "#id_factor"]},
    {"Factor": ["NUM", "#push_num"]},
    {"VarCallPrime": ["(", "Args", ")", "#func_call"]},
    {"VarCallPrime": ["VarPrime"]},
    {"VarPrime": ["[", "Expression", "]", "#array_access"]},
    {"VarPrime": []},
    {"FactorPrime": ["(", "Args", ")", "#func_call"]},
    {"FactorPrime": []},
    {"FactorZegond": ["(", "Expression", ")", "#paren_expr"]},
    {"FactorZegond": ["NUM", "#push_num"]},
    {"Args": ["ArgList", "#process_args"]},
    {"Args": []},
    {"ArgList": ["Expression", "#push_arg", "ArgListPrime"]},
    {"ArgListPrime": [",", "Expression", "#push_arg", "ArgListPrime"]},
    {"ArgListPrime": []},
]

# columns of the parsing table
cls = {
    ";",
    "break",
    "if",
    "endif",
    "else",
    "while",
    "return",
    "ID",
    "NUM",
    "<",
    "==",
    "+",
    "-",
    "*",
    "/",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    "int",
    "void",
    "=",
    "$",
    ","
}
non_terminals = {list(rule.keys())[0] for rule in grammar}

# Create a Scanner
scanner = Scanner("input.txt")

# Parsing table
# we make the parsing table as described below:
parsing_table = {row: {cl: None for cl in cls} for row in non_terminals}


def construct_parsing_table():
    for non_terminal in non_terminals:

        for i, rule in enumerate(grammar):  # Iterate through grammar rules

            if non_terminal == list(rule.keys())[0]:  # Check if the rule's LHS matches the non-terminal
                for cl in predict_sets[i + 1]:  # Iterate through terminals in the predictive set
                    parsing_table[non_terminal][cl] = i  # Map the rule index to the terminal
                    # the reason for the disparacy between i and i+1 is that the list and enumerate index start from 0, whereas
                    # the prediction sets are indexed starting from 1

        # we also add the synch entries as disscussed on page 15th of lecture note 5
        for cl in cls:
            if parsing_table[non_terminal][cl] is None and cl in follow_sets[non_terminal]:
                parsing_table[non_terminal][cl] = "synch"
            if parsing_table[non_terminal][cl] is None and cl in first_sets[non_terminal]:
                parsing_table[non_terminal][cl] = "synch"

            # Construct the parsing table


construct_parsing_table()

syntax_errors = []


def panic_mode_recovery(stack, lookahead, line_number, top_symbol=None, top_node=None, token_type=None, lexeme=None):
    # panic mode will diagnose the agenda along with documenting the correspong error. later based on the agenda, the correct action will be done.

    # reaching end of the input, but having the stack still non-empty

    if lookahead == "$" and len(stack) > 1:
        syntax_errors.append(f"#{line_number} : syntax error, Unexpected EOF")
        return lookahead, top_symbol, top_node, token_type, lexeme, "EOF"

    if top_symbol in non_terminals:
        # Check if parsing table entry is "synch"
        if parsing_table.get(top_symbol, {}).get(lookahead) == "synch":
            syntax_errors.append(f"#{line_number} : syntax error, missing {top_symbol}")
            return lookahead, top_symbol, top_node, token_type, lexeme, "non-terminal insert"


        else:
            # Skip tokens until a valid entry is found in the parsing table
            syntax_errors.append(f"#{line_number} : syntax error, illegal {lookahead}")
            return lookahead, top_symbol, top_node, token_type, lexeme, "lookahead skip"

    # If top_symbol is a terminal
    if top_symbol in cls:
        if top_symbol != lookahead:
            syntax_errors.append(f"#{line_number} : syntax error, missing {top_symbol}")
            return lookahead, top_symbol, top_node, token_type, lexeme, "terminal insert"

    #  Unexpected symbol (should not occur)
    else:
        syntax_errors.append(f"#{line_number} : syntax error, Unexpected {lookahead}")
        return lookahead, top_symbol, top_node, token_type, lexeme, "unnormal symbol"


def parse():
    """LL(1) Table-driven Parser with Panic Mode error handling."""
    root = Node("Program")  # Root of the parse tree
    # stack will contain pairs, where the first element of each pair is the node's name and the second one is it's adress.
    stack = [("$", None), ("Program", root)]  # Stack holds tuples: (symbol, corresponding tree node)
    lookahead, token_type, lexeme, line_number = scanner.get_next_token()  # Get the first token
    agenda = None
    dollar_node = None  # Placeholder for the $ node
    flag = 0  # flag shows wheather we should modify the variables (needed if an error has occured) or we can simply pop from the stack and have our
    # normal routines.
    top_symbol = None
    top_node = None  # address of the top_symbol's node

    # we implement the logic stated on page 6 of the lecture note 5

    while stack:

        if flag == 0:
            top_symbol, top_node = stack.pop()

        # as you see below, based on the agenda we make differnt desicions. details can be found on page 16th of the lecture note 5
        if flag == 1:

            if agenda == "EOF":
                while stack:
                    top_node.parent = None
                    top_symbol, top_node = stack.pop()
                return root

            elif agenda == "non-terminal insert":
                top_node.parent = None
                top_symbol, top_node = stack.pop()

            elif agenda == "terminal insert":
                top_node.parent = None
                top_symbol, top_node = stack.pop()

            elif agenda == "lookahead skip":
                lookahead, token_type, lexeme, line_number = scanner.get_next_token()

            else:
                lookahead, token_type, lexeme, line_number = scanner.get_next_token()

            flag = 0

        #  Terminal matches lookahead

        if top_symbol in cls:
            if top_symbol == "$":
                dollar_node = Node("$", parent=top_node)  # Create $ node but attach it later

            if top_symbol == lookahead:
                if top_symbol == "NUM":
                    semantic_stack.append(lexeme)  # Push number value
                elif top_symbol == "ID":
                    semantic_stack.append(lexeme)  # Push identifier name

                if top_symbol == "$":
                    dollar_node = Node("$", parent=top_node)  # Create $ node but attach it later

                elif top_node is not None and top_symbol not in {"$", "EOF"}:
                    # the name should be adjusted if top symbol is a terminal and match has happened.
                    top_node.name = f"({token_type}, {lexeme})"
                lookahead, token_type, lexeme, line_number = scanner.get_next_token()

            else:
                if top_symbol == "$":
                    break

                # Pass to panic mode recovery if terminal doesn't match
                lookahead, top_symbol, top_node, token_type, lexeme, agenda = panic_mode_recovery(stack, lookahead,
                                                                                                  line_number,
                                                                                                  top_symbol, top_node,
                                                                                                  token_type, lexeme)
                flag = 1
                continue


        # Non-terminal
        elif top_symbol in parsing_table and lookahead in parsing_table[top_symbol]:

            production_index = parsing_table[top_symbol][lookahead]

            # None valid produciton

            if production_index is None:

                lookahead, top_symbol, top_node, token_type, lexeme, agenda = panic_mode_recovery(stack, lookahead,
                                                                                                  line_number,
                                                                                                  top_symbol, top_node,
                                                                                                  token_type, lexeme)
                flag = 1
                continue

            # None valid produciton

            elif production_index == "synch":

                # Pass to panic mode recovery if the production is "synch"
                lookahead, top_symbol, top_node, token_type, lexeme, agenda = panic_mode_recovery(stack, lookahead,
                                                                                                  line_number,
                                                                                                  top_symbol, top_node,
                                                                                                  token_type, lexeme)
                flag = 1
                continue

            # valid produciton

            else:
                production = grammar[production_index]
                rhs = list(production.values())[0]  # we Get the RHS symbols as a list of strings

                # Process action symbols first
                for symbol in rhs:
                    if isinstance(symbol, str) and symbol.startswith('#'):
                        code_gen(symbol)  # Strip the '#' and call code generator

                if not rhs:  # handling Empty production
                    Node("epsilon", parent=top_node)
                else:
                    child_nodes = []  # Temporarily store child nodes
                    for symbol in rhs:
                        if isinstance(symbol, str) and symbol.startswith('#'):
                            continue  # Skip action symbols for tree nodes

                        child_node = None
                        if symbol in non_terminals:
                            child_node = Node(symbol, parent=top_node)
                            child_nodes.append((symbol, child_node))
                        else:
                            child_node = Node(f"({token_type}, {lexeme})", parent=top_node)
                            child_nodes.append((symbol, child_node))

                    # Push symbols onto the stack in reverse order for parsing
                    for symbol, child_node in reversed(child_nodes):
                        stack.append((symbol, child_node))

        #  No valid production
        else:

            lookahead, top_symbol, top_node, token_type, lexeme, agenda = panic_mode_recovery(stack, lookahead,
                                                                                              line_number)
            flag = 1
            continue

    # Attach the $ node at the end
    if dollar_node:
        dollar_node.parent = root

    return root


# funciton to write syntax errors to file
def write_syntax_errors_to_file():
    """Write syntax errors to a file."""
    with open("syntax_errors.txt", "w") as f:
        j = 0
        if syntax_errors:

            for error in syntax_errors:

                if j != 0:
                    f.write("\n")
                j = 1
                f.write(error)
        else:
            f.write("There is no syntax error.")


def get_temp():
    global temp_counter
    temp_counter += 1
    return f"t{temp_counter}"


def get_label():
    global label_counter
    label_counter += 1
    return f"L{label_counter}"


def allocate_memory(size=4):
    global memory_address
    memory_address += size
    return memory_address - size


# Add this class for symbol table entries
class SymbolEntry:
    def __init__(self, name, type_, address, scope, is_array=False, array_size=1):
        self.name = name
        self.type = type_
        self.address = address
        self.scope = scope
        self.is_array = is_array
        self.array_size = array_size


def code_gen(action_symbol):
    global current_scope, semantic_stack, symbol_table

    if action_symbol == "#program_end":
        output_code.append("(JP, @main,,)")  # Jump to main function
        return

    elif action_symbol == "#declare_id":
        # Get type and ID from semantic stack
        var_type = semantic_stack.pop()
        var_name = semantic_stack.pop()
        # Allocate memory and add to symbol table
        address = allocate_memory()
        symbol_table.append(SymbolEntry(var_name, var_type, address, current_scope))
        semantic_stack.append(address)

    elif action_symbol == "#var_decl_array":
        array_size = int(semantic_stack.pop())
        address = semantic_stack.pop()
        # Update symbol table entry with array info
        for entry in symbol_table:
            if entry.address == address:
                entry.is_array = True
                entry.array_size = array_size
                entry.type += "[]"
                break

    elif action_symbol == "#func_begin":
        func_name = semantic_stack.pop()
        # Allocate memory for return address
        return_address = allocate_memory()
        output_code.append(f"(ASSIGN, #{func_name}, {return_address},)")
        current_scope += 1

    elif action_symbol == "#func_end":
        current_scope -= 1
        # Generate return code
        output_code.append("(JP, @RET,,)")

    elif action_symbol == "#push_num":
        num_value = semantic_stack.pop()
        temp = get_temp()
        output_code.append(f"(ASSIGN, #{num_value}, {temp},)")
        semantic_stack.append(temp)

    elif action_symbol == "#add_sub":
        op2 = semantic_stack.pop()
        op1 = semantic_stack.pop()
        operator = semantic_stack.pop()
        temp = get_temp()

        if operator == "+":
            output_code.append(f"(ADD, {op1}, {op2}, {temp})")
        else:
            output_code.append(f"(SUB, {op1}, {op2}, {temp})")

        semantic_stack.append(temp)

    elif action_symbol == "#mult_div":
        op2 = semantic_stack.pop()
        op1 = semantic_stack.pop()
        operator = semantic_stack.pop()
        temp = get_temp()

        if operator == "*":
            output_code.append(f"(MULT, {op1}, {op2}, {temp})")
        else:
            output_code.append(f"(DIV, {op1}, {op2}, {temp})")

        semantic_stack.append(temp)

    elif action_symbol == "#relop":
        op2 = semantic_stack.pop()
        op1 = semantic_stack.pop()
        operator = semantic_stack.pop()
        temp = get_temp()

        if operator == "<":
            output_code.append(f"(LT, {op1}, {op2}, {temp})")
        else:
            output_code.append(f"(EO, {op1}, {op2}, {temp})")

        semantic_stack.append(temp)

    elif action_symbol == "#assign":
        value = semantic_stack.pop()
        target = semantic_stack.pop()
        output_code.append(f"(ASSIGN, {value}, {target},)")

    elif action_symbol == "#if_start":
        condition = semantic_stack.pop()
        false_label = get_label()
        semantic_stack.append(false_label)
        output_code.append(f"(JPF, {condition}, {false_label},)")

    elif action_symbol == "#else_jump":
        false_label = semantic_stack.pop()
        end_label = get_label()
        output_code.append(f"(JP, {end_label},,)")
        output_code.append(f"{false_label}:")
        semantic_stack.append(end_label)

    elif action_symbol == "#if_end":
        end_label = semantic_stack.pop()
        output_code.append(f"{end_label}:")

    elif action_symbol == "#while_start":
        start_label = get_label()
        semantic_stack.append(start_label)
        output_code.append(f"{start_label}:")

    elif action_symbol == "#while_cond":
        condition = semantic_stack.pop()
        end_label = get_label()
        semantic_stack.append(end_label)
        output_code.append(f"(JPF, {condition}, {end_label},)")

    elif action_symbol == "#while_end":
        end_label = semantic_stack.pop()
        start_label = semantic_stack.pop()
        output_code.append(f"(JP, {start_label},,)")
        output_code.append(f"{end_label}:")

    elif action_symbol == "#func_call":
        func_name = semantic_stack.pop()
        temp = get_temp()
        output_code.append(f"(ASSIGN, @{func_name}, {temp},)")
        output_code.append(f"(JP, {temp},,)")

    elif action_symbol == "#push_arg":
        arg = semantic_stack.pop()
        output_code.append(f"(ASSIGN, {arg}, @ARG,)")

    # Add more handlers for other action symbols as needed


# Add this function to write output to file
def write_output():
    with open("output.txt", "w") as f:
        for i, code in enumerate(output_code):
            f.write(f"{i}: {code}\n")


def main():
    """Main function to run the parser."""
    # Reset global states for new compilation
    global temp_counter, label_counter, semantic_stack, output_code
    temp_counter = 0
    label_counter = 0
    semantic_stack = []
    output_code = []
    parse_tree = None

    try:
        parse_tree = parse()
        write_output()
        if parse_tree:
            print("Parsing completed successfully!")
        else:
            print("Parsing failed.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        write_syntax_errors_to_file()

    if parse_tree:
        with open("parse_tree.txt", "w", encoding="utf-8") as f:
            i = 0

            # iterating over the tree to print it in the file
            for pre, _, node in RenderTree(parse_tree):
                if i != 0:
                    f.write(f"\n")
                i = 1
                f.write(f"{pre}{node.name}")


if __name__ == "__main__":
    main()