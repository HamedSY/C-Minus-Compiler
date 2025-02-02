from General.dicts import first_sets, follow_sets, predict_sets
from General.grammar import grammar
from scanner import Scanner

from anytree import RenderTree, Node


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
                if not rhs:  # handling Empty production
                    Node("epsilon", parent=top_node)
                else:
                    child_nodes = []  # Temporarily store child nodes
                    for symbol in rhs:
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


def main():
    """Main function to run the parser."""
    parse_tree = None
    try:
        parse_tree = parse()
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
