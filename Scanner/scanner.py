from General.dfa import get_next_state, accept_states, whitespace


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
