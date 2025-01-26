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


# Initialize output structures
tokens = []
errors = []
symbol_table = []
comment_stack = []
inside_comment = False

KEYWORDS = {"break", "else", "if", "endif", "int", "while", "return", "void"}

# Add keywords to the top of the symbol table
symbol_table.extend(KEYWORDS)


def add_token(line_num, token_type, lexeme):
    tokens.append((line_num, (token_type, lexeme)))
    if token_type == "ID" and lexeme not in symbol_table:
        symbol_table.append(lexeme)


def handle_error(line_num, error_message):
    errors.append((line_num, error_message))


# Scanner function to process each line
def get_next_token(line, line_num):
    index = 0
    current_state = 0
    lexeme = ""

    while index < len(line):
        global comment_stack, inside_comment
        char = line[index]
        next_state, is_included = get_next_state(current_state, char)

        if current_state == 6 and char == '*':
            first7chars = line[index - 1:index + 6]
            if first7chars.endswith('\n'):
                first7chars = first7chars[:-1]
            else:
                first7chars += '...'
            comment_stack.append((line_num, first7chars))
            inside_comment = True

        if next_state is None:
            error_found = False
            if accept_states[current_state]:
                if inside_comment:
                    if current_state == 9:  # Comment found
                        comment_stack.pop()
                        if not comment_stack:
                            inside_comment = False
                else:
                    if current_state == 1 or current_state == 2 or current_state == 6:  # Symbol found
                        add_token(line_num, "SYMBOL", lexeme)
                    elif current_state == 7:  # Number found
                        add_token(line_num, "NUM", lexeme)
                    elif current_state == 13:  # ID or keyword found
                        if lexeme in KEYWORDS:
                            add_token(line_num, "KEYWORD", lexeme)
                        else:
                            add_token(line_num, "ID", lexeme)
                    elif current_state == 12:  # Whitespace found
                        pass  # Ignore
            else:
                lexeme += char
                if current_state == 4:
                    handle_error(line_num, f"({lexeme}, Invalid number)")
                elif current_state == 14 and lexeme == '*/':
                    if comment_stack:
                        comment_stack.pop()
                        if not comment_stack:
                            inside_comment = False  # We're exiting the block comment
                    else:
                        handle_error(line_num, "(*/, Unmatched comment)")
                else:
                    handle_error(line_num, f"({lexeme}, Invalid input)")

                error_found = True

            # Reset for the next token
            lexeme = ""
            current_state = 0
            if char in whitespace or error_found:
                index += 1
            continue

        if is_included:
            lexeme += char
            index += 1
        current_state = next_state


# End of file check for unclosed comments
def check_unclosed_comments():
    if comment_stack:
        # Add the first unclosed comment as an error
        handle_error(comment_stack[0][0], f"({comment_stack[0][1]}, Unclosed comment)")


# Main function to process file line-by-line
def scan_file(input_file):
    line_num = 1
    with open(input_file, 'r') as file:
        for line in file:
            get_next_token(line, line_num)
            line_num += 1
    check_unclosed_comments()


# Output functions
def save_tokens(output_file="tokens.txt"):
    with open(output_file, 'w') as file:
        current_line = None
        for line_num, token in tokens:
            if line_num != current_line:
                if current_line is not None:
                    file.write("\n")
                file.write(f"{line_num}.\t")
                current_line = line_num
            token_type, lexeme = token
            file.write(f"({token_type}, {lexeme}) ")


def save_errors(output_file="lexical_errors.txt"):
    with open(output_file, 'w') as file:
        if not errors:
            file.write("There is no lexical error.\n")
        else:
            current_line = None
            for line_num, error in errors:
                if line_num != current_line:
                    if current_line is not None:
                        file.write("\n")
                    file.write(f"{line_num}.\t")
                    current_line = line_num
                file.write(f"{error} ")


def save_symbol_table(output_file="symbol_table.txt"):
    with open(output_file, 'w') as file:
        for index, symbol in enumerate(symbol_table, 1):
            file.write(f"{index}.\t{symbol}\n")


if __name__ == "__main__":
    input_file = "input.txt"
    scan_file(input_file)
    save_tokens()
    save_errors()
    save_symbol_table()