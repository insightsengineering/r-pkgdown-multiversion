"""
Multi-version dropdown updater.
"""

import argparse
import os
import re
import sys
import shutil
import logging
from pathlib import Path

from lxml import etree, html
from packaging.version import InvalidVersion, Version

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def compile_pattern(pattern):
    """
    Compile the given regular expression pattern.

    :param pattern: A regular expression pattern to match directory names.
    :return: Compiled regex pattern.
    """
    logger.debug(f"Compiling pattern: {pattern}")
    try:
        compiled = re.compile(pattern)
        logger.debug(f"Successfully compiled pattern: {compiled.pattern}")
        return compiled
    except Exception as e:
        logger.error(f"Failed to compile pattern: {e}")
        raise


def find_matching_directories(directory, regex):
    """
    Find all matching directories in the given directory based on the regex pattern.

    :param directory: The root directory to search for matching directories.
    :param regex: Compiled regular expression pattern to match directory names.
    :return: List of matching directories.
    """
    logger.debug(f"Searching in directory: {directory}")
    logger.debug(f"Using regex pattern: {regex.pattern}")

    all_dirs = [
        d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))
    ]
    logger.debug(f"Found directories: {all_dirs}")

    matching_dirs = []
    for d in all_dirs:
        match = regex.match(d)
        logger.debug(f"Testing directory '{d}': {'matches' if match else 'no match'}")
        if match:
            matching_dirs.append(d)

    logger.debug(f"Matching directories: {matching_dirs}")
    return matching_dirs


def separate_refs(matching_dirs, refs_order):
    """
    Separate items in refs_order and other items for semantic versioning sorting.

    :param matching_dirs: List of matching directories.
    :param refs_order: List determining the order of items to appear at the beginning.
    :return: Tuple of ordered_refs and remaining_refs.
    """
    ordered_refs = [d for d in refs_order if d in matching_dirs]
    remaining_refs = [d for d in matching_dirs if d not in refs_order]
    logger.debug(
        f"Separated refs - ordered: {ordered_refs}, remaining: {remaining_refs}"
    )
    return ordered_refs, remaining_refs


def sorting_key(ref):
    """
    Define a custom sorting key function.

    :param ref: Reference to be sorted.
    :return: Tuple for sorting.
    """
    try:
        # Handle versions with 'v' prefix
        version_str = ref[1:] if ref.startswith("v") else ref
        return (0, Version(version_str))
    except InvalidVersion:
        logger.debug(f"'{ref}' is not a valid semantic version")
        return (1, ref)


def sort_remaining_refs(remaining_refs):
    """
    Sort the remaining items using the custom sorting key
    (semantic versioning first, then alphabetically).

    :param remaining_refs: List of remaining references.
    :return: Sorted list of remaining references.
    """
    logger.debug(f"Sorting remaining refs: {remaining_refs}")
    remaining_refs.sort(key=sorting_key, reverse=True)
    logger.debug(f"Sorted remaining refs: {remaining_refs}")
    return remaining_refs


def generate_refs_dict(ordered_refs, base_url):
    """
    Generate the full URLs for the directories.

    :param ordered_refs: List of ordered references.
    :param base_url: The base URL to be used in the hrefs.
    :return: Dictionary of references and their URLs.
    """
    refs_dict = {ref: f"{base_url}{ref}" for ref in ordered_refs}
    logger.debug(f"Generated refs dictionary: {refs_dict}")
    return refs_dict


def generate_markup(ordered_refs, refs_dict):
    """
    Generate the HTML markup for the drop-down list.

    :param ordered_refs: List of ordered references.
    :param refs_dict: Dictionary of references and their URLs.
    :return: str, Generated HTML markup.
    """
    logger.debug(f"Generating markup for {len(ordered_refs)} refs")
    logger.debug(f"Refs to include: {ordered_refs}")

    nav_item = """
    <li class="nav-item dropdown">
    <a href="#" class="nav-link dropdown-toggle"
        data-bs-toggle="dropdown" role="button"
        aria-expanded="false" aria-haspopup="true"
        id="dropdown-versions">Versions</a>
    <div class="dropdown-menu" aria-labelledby="dropdown-versions">
    """
    for ref in ordered_refs:
        nav_item += '<a class="dropdown-item" data-toggle="tooltip" title="" '
        nav_item += f'href="{refs_dict[ref]}">{ref}</a>\n'
    nav_item += "</div></li>"

    logger.debug(f"Generated nav item: {nav_item}")
    return nav_item


def find_navbar(tree):
    """
    Find the first <ul> element in the document that contains the class 'navbar-nav'.

    :param tree: lxml HTML tree object.
    :return: First <ul> element with class 'navbar-nav' or None.
    """
    logger.debug("Searching for navbar")

    # Try the original XPath
    navbar = tree.xpath(
        "//div[@id='navbar']//ul[contains(@class, 'navbar-nav') and contains(@class, 'me-auto')]"
    )

    if navbar:
        logger.debug(f"Found navbar with original XPath: {navbar[0].get('class')}")
        return navbar[0]

    # Try alternative XPath patterns
    alternative_patterns = [
        "//ul[contains(@class, 'navbar-nav')]",
        "//nav//ul[contains(@class, 'navbar-nav')]",
        "//div[contains(@class, 'navbar')]//ul[contains(@class, 'navbar-nav')]",
    ]

    for pattern in alternative_patterns:
        logger.debug(f"Trying alternative pattern: {pattern}")
        navbar = tree.xpath(pattern)
        if navbar:
            logger.debug(
                f"Found navbar with pattern '{pattern}': {navbar[0].get('class')}"
            )
            return navbar[0]

    logger.error("No navbar found with any pattern")
    return None


def find_navbar_items(navbar):
    """
    Find <li> elements representing items in the navbar.

    :param navbar: The navbar.
    :return: List of <li> elements.
    """
    if navbar or navbar is not None:
        items = navbar.xpath('.//li[contains(@class, "nav-item")]')
        logger.debug(f"Found {len(items)} navbar items")
        return items
    logger.error("No navbar provided to find items")
    return []


def create_versions_dropdown(dropdown_list):
    """
    Create a new element from the drop-down list markup.

    :param dropdown_list: str, HTML markup containing the drop-down list to insert.
    :return: Custom element or None.
    """
    try:
        return html.fromstring(dropdown_list, parser=etree.HTMLParser())
    except Exception as e:
        logger.error(f"Error parsing the drop-down list: {e}")
        return None


def insert_versions_dropdown(tree, dropdown_list):
    """
    Inserts the drop-down list into the navbar.

    :param tree: lxml HTML tree object.
    :param dropdown_list: str, HTML markup containing the drop-down list to insert.
    :return: bool, True if successful, False otherwise.
    """
    logger.debug("Attempting to insert dropdown")

    navbar = find_navbar(tree)
    if not navbar:
        logger.error("No navbar found in the document")
        return False

    navbar_items = find_navbar_items(navbar)
    if not navbar_items:
        logger.error("No navbar items found")
        return False

    versions_dropdown = create_versions_dropdown(dropdown_list)
    if not versions_dropdown:
        logger.error("Failed to create dropdown element")
        return False

    # Find all <li> that contain a <div> with aria-labelledby="dropdown-versions"
    existing_dropdown = navbar.xpath('.//li[div/@aria-labelledby="dropdown-versions"]')
    logger.debug(f"Found {len(existing_dropdown)} existing dropdowns")

    # If no existing dropdown is found, add the new dropdown to the end of the navbar
    if not existing_dropdown:
        logger.debug("No existing dropdown found, adding new one")
        new_li = html.Element("div")
        new_li.append(versions_dropdown)
        navbar[-1].addnext(new_li)
        return True

    # Remove duplicates by keeping track of IDs or contents
    existing_ids = set()
    for item in existing_dropdown:
        dropdown_id = item.get("id")
        if dropdown_id not in existing_ids:
            existing_ids.add(dropdown_id)
        else:
            logger.debug(f"Removing duplicate dropdown with id {dropdown_id}")
            item.getparent().remove(item)

    # Replace the first remaining existing dropdown with the new versions_dropdown
    if existing_dropdown:
        logger.debug("Replacing existing dropdown")
        existing_dropdown[0].getparent().replace(
            existing_dropdown[0], versions_dropdown
        )

    return True


def read_file(file_path):
    """
    Read the content of a file.

    :param file_path: Path to the file.
    :return: Content of the file or None.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"The file '{file_path}' was not found.")
    except PermissionError:
        logger.error(f"Permission denied to read the file '{file_path}'.")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while reading the file '{file_path}': {e}"
        )
    return None


def write_file(file_path, content):
    """
    Write content to a file.

    :param file_path: Path to the file.
    :param content: Content to write.
    :return: bool, True if successful, False otherwise.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except PermissionError:
        logger.error(f"Permission denied to write to the file '{file_path}'.")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while writing to the file '{file_path}': {e}"
        )
    return False


def process_single_html_file(file_path, dropdown_list):
    """
    Process a single HTML file, inserting a dropdown list after the last <li> element.

    :param file_path: Path to the HTML file.
    :param dropdown_list: HTML content for the dropdown list.
    :return: bool, True if successful, False otherwise.
    """
    logger.debug(f"Processing file: {file_path}")

    html_contents = read_file(file_path)
    if html_contents is None:
        return False

    try:
        tree = html.fromstring(html_contents)
    except etree.XMLSyntaxError as e:
        logger.error(f"Error parsing the HTML: {e}")
        return False

    success = insert_versions_dropdown(tree, dropdown_list)
    if not success:
        logger.error(f"Failed to process {file_path}")
        return False

    doctype = "<!DOCTYPE html>\n"
    comment = "<!-- Generated by pkgdown + https://github.com/insightsengineering/r-pkgdown-multiversion -->\n"
    html_content = etree.tostring(
        tree, encoding="unicode", pretty_print=True, method="html"
    )
    modified_html = doctype + comment + html_content

    if not write_file(file_path, modified_html):
        return False

    logger.info(f"Successfully processed {file_path}")
    return True


def generate_dropdown_list(directory, pattern, refs_order, base_url):
    """
    Generates version drop-down list to be inserted based
    on matching directories in the given directory and refs_order.

    :param directory: The root directory to search for matching directories.
    :param pattern: A regular expression pattern to match directory names.
    :param refs_order: List determining the order of items to appear at the beginning.
    :param base_url: The base URL to be used in the hrefs.
    :return: str, Generated HTML markup.
    """
    logger.debug("Starting generate_dropdown_list")
    logger.debug(f"Directory: {directory}")
    logger.debug(f"Pattern: {pattern}")
    logger.debug(f"Refs order: {refs_order}")
    logger.debug(f"Base URL: {base_url}")

    regex = compile_pattern(pattern)
    matching_dirs = find_matching_directories(directory, regex)

    logger.debug(f"Found {len(matching_dirs)} matching directories")

    ordered_refs, remaining_refs = separate_refs(matching_dirs, refs_order)
    logger.debug(f"Ordered refs: {ordered_refs}")
    logger.debug(f"Remaining refs before sorting: {remaining_refs}")

    remaining_refs = sort_remaining_refs(remaining_refs)
    logger.debug(f"Remaining refs after sorting: {remaining_refs}")

    ordered_refs.extend(remaining_refs)
    logger.debug(f"Final ordered refs: {ordered_refs}")

    refs_dict = generate_refs_dict(ordered_refs, base_url)
    logger.debug(f"Generated refs dict: {refs_dict}")

    markup = generate_markup(ordered_refs, refs_dict)
    logger.debug(f"Generated markup: {markup}")
    return markup


def process_html_files_in_directory(directory, pattern, refs_order, base_url):
    """
    Process all HTML files in the given directory,
    inserting a dropdown list after the last <li> element.

    :param directory: The root directory to search for HTML files.
    :param pattern: Regular expression pattern to match directory names.
    :param refs_order: List determining the order of items to appear at the beginning.
    :param base_url: Base URL to be used in the hrefs.
    """
    logger.info(f"Processing HTML files in directory: {directory}")
    processed_files = set()
    dropdown_list = generate_dropdown_list(directory, pattern, refs_order, base_url)

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                if file_path in processed_files:
                    continue

                if process_single_html_file(file_path, dropdown_list):
                    processed_files.add(file_path)


def update_single_search_json(search_json_path, version, base_url):
    """
    Update the URLs in a single search.json file to include the version.

    :param search_json_path: Path to the search.json file.
    :param version: Version to be included in the URLs.
    :param base_url: Base URL to be used in the hrefs.
    :return: bool, True if successful, False otherwise.
    """
    logger.debug(f"Updating search.json: {search_json_path}")
    file_content = read_file(search_json_path)
    if file_content is None:
        return False

    url_pattern = re.compile(rf"({re.escape(base_url)})(?!{re.escape(version)})")
    updated_content = url_pattern.sub(f"{base_url}{version}/", file_content)

    if updated_content != file_content:
        if write_file(search_json_path, updated_content):
            logger.info(f"Updated URLs in {search_json_path}")
            return True
        logger.error(f"Failed to update URLs in {search_json_path}")
        return False
    logger.debug(f"No URLs to update in {search_json_path}")
    return True


def update_search_json_urls(directory, pattern, base_url):
    """
    Update the URLs in search.json files within the given directory to include the version.

    :param directory: The root directory to search for search.json files.
    :param pattern: Regular expression pattern to match directory names.
    :param base_url: Base URL to be used in the hrefs.
    """
    logger.info(f"Updating search.json URLs in directory: {directory}")
    regex = compile_pattern(pattern)
    matching_dirs = find_matching_directories(directory, regex)

    for current_directory in matching_dirs:
        search_json_path = os.path.join(directory, current_directory, "search.json")
        if not os.path.isfile(search_json_path):
            continue

        update_single_search_json(search_json_path, current_directory, base_url)


def find_latest_version_tag(directory):
    """
    Find the latest version tag in the directory.

    :param directory: Directory to search in
    :return: Tuple of (latest_tag, latest_rc_tag)
    """
    try:
        dirs = [
            d
            for d in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, d))
        ]

        # Find latest version tag
        version_pattern = re.compile(r"^v([0-9]+\.)?([0-9]+\.)?([0-9]+)$")
        version_dirs = [d for d in dirs if version_pattern.match(d)]

        latest_tag = None
        if version_dirs:
            # Sort by version number
            def version_sort_key(v):
                # Remove 'v' prefix and split by dots
                version_str = v[1:] if v.startswith("v") else v
                try:
                    return Version(version_str)
                except InvalidVersion:
                    return Version("0.0.0")

            latest_tag = sorted(version_dirs, key=version_sort_key)[-1]

        # Find latest release candidate tag
        rc_pattern = re.compile(r"^v([0-9]+\.)?([0-9]+\.)?([0-9]+)(-rc[0-9]+)$")
        rc_dirs = [d for d in dirs if rc_pattern.match(d)]

        latest_rc_tag = None
        if rc_dirs:
            latest_rc_tag = sorted(rc_dirs, key=version_sort_key)[-1]

        return latest_tag, latest_rc_tag
    except Exception as e:
        logger.error(f"Error finding latest tags: {e}")
        return None, None


def update_search_json_in_directory(directory, old_name, new_name):
    """
    Update search.json file in a directory to replace old_name with new_name.

    :param directory: Directory containing search.json
    :param old_name: Old name to replace
    :param new_name: New name to replace with
    :return: bool, True if successful
    """
    search_json_path = os.path.join(directory, "search.json")
    if not os.path.exists(search_json_path):
        return True  # No search.json to update

    try:
        with open(search_json_path, "r", encoding="utf-8") as f:
            content = f.read()

        updated_content = content.replace(old_name, new_name)

        with open(search_json_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        logger.info(f"Updated search.json in {directory}: {old_name} -> {new_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating search.json in {directory}: {e}")
        return False


def create_tag_copies(directory, latest_tag_alt_name="", release_candidate_alt_name=""):
    """
    Create copies of latest tag and release candidate directories.

    :param directory: Root directory
    :param latest_tag_alt_name: Alternative name for latest tag
    :param release_candidate_alt_name: Alternative name for release candidate
    :return: bool, True if successful
    """
    try:
        os.chdir(directory)

        latest_tag, latest_rc_tag = find_latest_version_tag(".")

        # Remove existing directories
        for dir_name in ["latest-tag", "release-candidate"]:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)

        # Create latest-tag copy
        if latest_tag:
            shutil.copytree(latest_tag, "latest-tag")
            update_search_json_in_directory("latest-tag", latest_tag, "latest-tag")
            logger.info(f"Created latest-tag from {latest_tag}")
        else:
            logger.warning("No latest tag found, not creating directory for latest-tag")

        # Create release-candidate copy
        if latest_rc_tag:
            shutil.copytree(latest_rc_tag, "release-candidate")
            update_search_json_in_directory(
                "release-candidate", latest_rc_tag, "release-candidate"
            )
            logger.info(f"Created release-candidate from {latest_rc_tag}")
        else:
            logger.warning(
                "No release candidate tag found, not creating directory for release-candidate"
            )

        # Create alt-name copies with correct search.json updates
        if latest_tag_alt_name and os.path.exists("latest-tag"):
            if os.path.exists(latest_tag_alt_name):
                shutil.rmtree(latest_tag_alt_name)
            shutil.copytree("latest-tag", latest_tag_alt_name)
            # Fix the bug: update search.json to use alt-name instead of "latest-tag"
            update_search_json_in_directory(
                latest_tag_alt_name, "latest-tag", latest_tag_alt_name
            )
            logger.info(f"Created {latest_tag_alt_name} from latest-tag")

        if release_candidate_alt_name and os.path.exists("release-candidate"):
            if os.path.exists(release_candidate_alt_name):
                shutil.rmtree(release_candidate_alt_name)
            shutil.copytree("release-candidate", release_candidate_alt_name)
            # Fix the bug: update search.json to use alt-name instead of "release-candidate"
            update_search_json_in_directory(
                release_candidate_alt_name,
                "release-candidate",
                release_candidate_alt_name,
            )
            logger.info(f"Created {release_candidate_alt_name} from release-candidate")

        return True
    except Exception as e:
        logger.error(f"Error creating tag copies: {e}")
        return False


def create_redirect_page(
    directory, default_landing_page, repository_name, repository_owner, action_path
):
    """
    Create redirect page (index.html) and .nojekyll file.

    :param directory: Root directory
    :param default_landing_page: Default landing page
    :param repository_name: Repository name
    :param repository_owner: Repository owner
    :param action_path: Path to action files
    :return: bool, True if successful
    """
    try:
        os.chdir(directory)

        # Copy redirect.html to index.html
        redirect_source = os.path.join(action_path, "redirect.html")
        if os.path.exists(redirect_source):
            shutil.copy2(redirect_source, "index.html")
        else:
            # Create a basic redirect page if redirect.html doesn't exist
            redirect_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Redirecting...</title>
    <meta http-equiv="refresh" content="0; url=./{default_landing_page}/">
    <link rel="canonical" href="./{default_landing_page}/">
</head>
<body>
    <p>If you are not redirected automatically, <a href="./{default_landing_page}/">click here</a>.</p>
</body>
</html>"""
            with open("index.html", "w", encoding="utf-8") as f:
                f.write(redirect_content)

        # Update placeholders in index.html
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace("DEFAULT_LANDING_PAGE", default_landing_page)
        content = content.replace("REPOSITORY", repository_name)
        content = content.replace("OWNER", repository_owner)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(content)

        # Create .nojekyll file
        Path(".nojekyll").touch()

        logger.info("Created redirect page and .nojekyll file")
        return True
    except Exception as e:
        logger.error(f"Error creating redirect page: {e}")
        return False


def create_root_pkgdown_yml(directory, default_landing_page):
    """
    Create root-level pkgdown.yml file.

    :param directory: Root directory
    :param default_landing_page: Default landing page
    :return: bool, True if successful
    """
    try:
        os.chdir(directory)

        source_pkgdown = os.path.join(default_landing_page, "pkgdown.yml")
        if os.path.exists(source_pkgdown):
            shutil.copy2(source_pkgdown, "pkgdown.yml")

            # Update paths in pkgdown.yml
            with open("pkgdown.yml", "r", encoding="utf-8") as f:
                content = f.read()

            # Use regex to update paths, avoiding the default landing page path
            pattern = (
                rf"(/(?:reference|articles))(?!/{re.escape(default_landing_page)})"
            )
            replacement = rf"/{default_landing_page}\1"
            updated_content = re.sub(pattern, replacement, content)

            with open("pkgdown.yml", "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"Created root-level pkgdown.yml from {default_landing_page}")
        else:
            logger.warning(f"No pkgdown.yml found in {default_landing_page}")

        return True
    except Exception as e:
        logger.error(f"Error creating root-level pkgdown.yml: {e}")
        return False


def main():
    """Main."""
    parser = argparse.ArgumentParser(
        description="Insert the multi-version drop-down list after the n-th <li>"
        "item in unordered lists in all HTML files within a directory."
    )
    parser.add_argument(
        "directory", help="Path to the directory containing HTML files."
    )
    parser.add_argument(
        "--pattern",
        required=True,
        help="Regular expression pattern to match directory names.",
    )
    parser.add_argument(
        "--refs_order",
        nargs="+",
        required=True,
        help="List determining the order of items to appear at the beginning.",
    )
    parser.add_argument(
        "--base_url", required=True, help="Base URL to be used in the hrefs."
    )
    parser.add_argument(
        "--default_landing_page", help="Default landing page branch/tag."
    )
    parser.add_argument("--repository_name", help="Repository name.")
    parser.add_argument("--repository_owner", help="Repository owner.")
    parser.add_argument("--action_path", help="Path to GitHub action files.")
    parser.add_argument(
        "--latest_tag_alt_name", default="", help="Alternative name for latest tag."
    )
    parser.add_argument(
        "--release_candidate_alt_name",
        default="",
        help="Alternative name for release candidate.",
    )
    parser.add_argument(
        "--setup_only",
        action="store_true",
        help="Only run setup steps, skip HTML processing.",
    )

    args = parser.parse_args()

    # Run setup steps if requested
    if args.setup_only or (
        args.default_landing_page and args.repository_name and args.repository_owner
    ):
        logger.info("Running setup steps...")

        # Step 1: Create tag copies
        if not create_tag_copies(
            args.directory, args.latest_tag_alt_name, args.release_candidate_alt_name
        ):
            logger.error("Failed to create tag copies")
            return 1

        # Step 2: Create redirect page
        if args.default_landing_page and args.repository_name and args.repository_owner:
            if not create_redirect_page(
                args.directory,
                args.default_landing_page,
                args.repository_name,
                args.repository_owner,
                args.action_path or "",
            ):
                logger.error("Failed to create redirect page")
                return 1

        # Step 3: Create root-level pkgdown.yml
        if args.default_landing_page:
            if not create_root_pkgdown_yml(args.directory, args.default_landing_page):
                logger.error("Failed to create root-level pkgdown.yml")
                return 1

    # Skip HTML processing if setup_only is True
    if args.setup_only:
        logger.info("Setup completed. Skipping HTML processing.")
        return 0

    # Run HTML processing steps
    process_html_files_in_directory(
        args.directory, args.pattern, args.refs_order, args.base_url
    )
    update_search_json_urls(args.directory, args.pattern, args.base_url)

    return 0


if __name__ == "__main__":
    sys.exit(main())
