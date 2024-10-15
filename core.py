import argparse
import os
import sys
import re
from lxml import etree, html
from packaging.version import Version, InvalidVersion

def generate_dropdown_list(directory, pattern, refs_order, base_url):
    """
    Generates version drop-down list to be inserted based on matching directories in the given directory
    and refs_order.

    :param directory: The root directory to search for matching directories.
    :param pattern: A regular expression pattern to match directory names.
    :param refs_order: List determining the order of items to appear at the beginning.
    :param base_url: The base URL to be used in the hrefs.
    :return: str, Generated HTML markup.
    """

    # Compile the pattern
    regex = re.compile(pattern)

    # Find all matching directories
    matching_dirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d)) and regex.match(d)]

    # Separate items in refs_order and other items for semantic versioning sorting
    ordered_refs = [d for d in refs_order if d in matching_dirs]
    remaining_refs = [d for d in matching_dirs if d not in refs_order]

    # Define a custom sorting key function
    def sorting_key(ref):
        try:
            return (0, Version(ref))
        except InvalidVersion:
            return (1, ref)

    # Sort the remaining items using the custom sorting key (semantic versioning first, then alphabetically)
    remaining_refs.sort(key=sorting_key, reverse=True)

    # Combine the ordered and remaining items
    ordered_refs.extend(remaining_refs)

    # Generate the full URLs for the directories
    refs_dict = {ref: f'{base_url}{ref}' for ref in ordered_refs}

    # Generate the markup
    nav_item = '''
    <li class="nav-item dropdown">
    <a href="#" class="nav-link dropdown-toggle" data-bs-toggle="dropdown" role="button" aria-expanded="false" aria-haspopup="true" id="dropdown-versions">Versions</a>
    <div class="dropdown-menu" aria-labelledby="dropdown-versions">
    '''
    for ref in ordered_refs:
        nav_item += f'<a class="dropdown-item" data-toggle="tooltip" title="" href="{refs_dict[ref]}">{ref}</a>\n'
    nav_item += '</div></li>'

    return nav_item

def insert_html_after_nth_li(tree, dropdown_list, n):
    """
    Inserts the drop-down list after the n-th <li> item in the unordered list.

    :param tree: lxml HTML tree object.
    :param dropdown_list: str, HTML markup containing the drop-down list to insert.
    :param n: int, Position after which the drop-down list will be inserted (0-based).
    """

    # Find <li> elements representing items in the nav-bar.
    li_elements = tree.xpath('//ul/li[contains(@class, "nav-item")]')

    if n < len(li_elements):
        # Create a new element from the drop-down list markup
        try:
            custom_element = html.fromstring(dropdown_list)
        except Exception as e:
            print(f"Error parsing the drop-down list: {e}", file=sys.stderr)
            return False

        # Get the n-th element
        nth_li = li_elements[n]

        # Insert the custom element after the n-th element
        nth_li.addnext(custom_element)

    return True

def process_html_files_in_directory(directory, pattern, refs_order, n, base_url):
    processed_files = set()

    # Generate the drop-down list
    dropdown_list = generate_dropdown_list(directory, pattern, refs_order, base_url)

    # Find all HTML files in the directory and subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)

                # Avoid processing the same file twice
                if file_path in processed_files:
                    continue

                # Read the input HTML file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        input_html = f.read()
                except FileNotFoundError:
                    print(f"Error: The file '{file_path}' was not found.", file=sys.stderr)
                    continue
                except PermissionError:
                    print(f"Error: Permission denied to read the file '{file_path}'.", file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"An unexpected error occurred while reading the file '{file_path}': {e}", file=sys.stderr)
                    continue

                # Parse the HTML content
                try:
                    tree = html.fromstring(input_html)
                except html.XMLSyntaxError as e:
                    print(f"Error parsing the HTML: {e}", file=sys.stderr)
                    continue

                # TODO Debug - remove
                # print('==================================================================')
                # print(file_path)
                # for li in tree.xpath('//ul/li[contains(@class, "nav-item")]'):
                #     print(etree.tostring(li, pretty_print=True, encoding='unicode'))
                #     print('------------')

                # Insert the drop-down list
                success = insert_html_after_nth_li(tree, dropdown_list, n)

                if not success:
                    print(f"❌ {file_path}", file=sys.stderr)
                    continue

                # Convert the modified part back to string and update the file.
                modified_html = etree.tostring(tree, encoding='unicode', pretty_print=True, method='html')

                # Write the result to the output file (overwrite the input file)
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_html)
                except PermissionError:
                    print(f"Error: Permission denied to write to the file '{file_path}'.", file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"An unexpected error occurred while writing to the file '{file_path}': {e}", file=sys.stderr)
                    continue

                print(f"✅ {file_path}")

                # Mark this file as processed
                processed_files.add(file_path)

def main():
    parser = argparse.ArgumentParser(description='Insert the multi-version drop-down list after the n-th <li> item in unordered lists in all HTML files within a directory.')
    parser.add_argument('directory', help='Path to the directory containing HTML files.')
    parser.add_argument('--pattern', required=True, help='Regular expression pattern to match directory names.')
    parser.add_argument('--refs_order', nargs='+', required=True, help='List determining the order of items to appear at the beginning.')
    parser.add_argument('--n', type=int, required=True, help='Position after which the drop-down list will be inserted (0-based).')
    parser.add_argument('--base_url', required=True, help='Base URL to be used in the hrefs.')

    args = parser.parse_args()

    # Process all HTML files in the specified directory
    process_html_files_in_directory(args.directory, args.pattern, args.refs_order, args.n, args.base_url)

if __name__ == '__main__':
    main()
