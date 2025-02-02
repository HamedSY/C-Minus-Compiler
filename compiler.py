from anytree import RenderTree
from Paser.parser import parse, write_syntax_errors_to_file
from CodeGeneration.code_gen import flush_outputs


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

        flush_outputs()


if __name__ == "__main__":
    main()
