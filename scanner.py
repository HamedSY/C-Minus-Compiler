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

