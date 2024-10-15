#!/usr/bin/env Rscript

# -------------------------------------------------------------
# Define constants for start and end tags for the dropdown menu
# -------------------------------------------------------------
# Mark the beginning of the dropdown menu for versions in the HTML file
start_tag <- "<!-- start dropdown for versions -->"
# Mark the end of the dropdown menu for versions in the HTML file
end_tag <- "<!-- end dropdown for versions -->"

# -----------------------------------------------------
# Extract the repository name from environment variables
# -----------------------------------------------------
# Extracts the repository name by removing the owner's name from the full repository path
repo_name <-
  gsub(
    paste0(Sys.getenv("GITHUB_REPOSITORY_OWNER"), "/"),
    "",
    Sys.getenv("GITHUB_REPOSITORY")
  )

# Construct the base URL for the repository by combining the owner's name, the repository name, and the GitHub Pages domain
base_url <- paste0(
  "https://",
  Sys.getenv("GITHUB_REPOSITORY_OWNER"),
  ".github.io/",
  repo_name
)

# Define the name of the search index file
search_index_file <- "search.json"

# ---------------------------------------------------
# Define a function to handle missing references list
# ---------------------------------------------------
# This function takes a list of references as input and returns a regular expression pattern to match them
# If the input is empty, it returns a default pattern that matches any string except those ending with ".git"
handle_missing_refs_list <- function(refs_to_list) {
  if (refs_to_list == "") {
    return("^(?!\\.git$).+$")
  }
  return(refs_to_list)
}

# -------------------------------------------------------------
# Define a function to filter versions based on a given pattern
# -------------------------------------------------------------
filter_versions <- function(refs_to_list = paste(
                              "^main$",
                              "^devel$",
                              "^pre-release$",
                              "^latest-tag$",
                              "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                              sep = "|"
                            )) {
  # List all directories in the current path, sorts them in descending order, and stores them in the 'versions' vector
  versions <- sort(
    list.dirs(
      path = ".",
      recursive = FALSE,
      full.names = FALSE
    ),
    decreasing = TRUE
  )

  # Filter the 'versions' vector based on the pattern provided in 'refs_to_list' and returns the filtered vector
  return(versions[
    grep(
      handle_missing_refs_list(refs_to_list),
      versions,
      perl = TRUE
    )
  ])
}

# -----------------------------------------------------------
# Define a function to update search indexes for each version
# -----------------------------------------------------------
update_search_indexes <- function(refs_to_list = paste(
                                    "^main$",
                                    "^devel$",
                                    "^pre-release$",
                                    "^latest-tag$",
                                    "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                                    sep = "|"
                                  )) {
  # Filter the versions based on the provided pattern
  versions <- filter_versions(refs_to_list)

  # Save the current working directory
  oldwd <- getwd()

  for (version in versions) {
    # Change the working directory to the current version directory
    setwd(version)

    # Update the indexes
    if (file.exists(search_index_file)) {
      # Read the contents of the search index file into a vector
      search_index <- readLines(search_index_file)

      # Update the search index by replacing the base URL with the version-specific URL
      updated_index <- gsub(
        paste0(base_url, "(?!/", version, ")"),
        paste0(base_url, "/", version),
        search_index,
        perl = TRUE
      )

      # Write the updated search index back to the file
      writeLines(updated_index, search_index_file)
    }
    # Reset the working directory to the original directory
    setwd(oldwd)
  }
}

# -------------------------------------------------------------
# Define a function to prepare the dropdown button for versions
# -------------------------------------------------------------
prepare_dropdown_button <- function(
    refs_to_list = paste(
      "^main$",
      "^devel$",
      "^pre-release$",
      "^latest-tag$",
      "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
      sep = "|"
    ),
    refs_order = c(
      "devel",
      "pre-release",
      "main",
      "latest-tag"
    ),
    version_tab = "") {
  # Evaluate the version tab configuration string into a list
  conf <- eval(parse(text = version_tab))

  # Filter versions according to refs_to_list
  versions <- filter_versions(refs_to_list)

  # Initialize an empty vector to store the ordered versions
  output <- c()

  # Iterate over the ordered references and appends the matching versions to the 'output' vector
  for (ref in refs_order) {
    result <- versions[grep(ref, versions)]
    if (!identical(result, character(0))) {
      output <- c(output, result)
    }
  }

  # Filter out versions that do not match any of the ordered references
  other_versions <-
    versions[!grepl(
      paste0(refs_order, collapse = "|"),
      versions
    )]

  # Append versions other than ones in refs_order
  # at the bottom of drop-down list
  # Sorting is done according to the number of characters:
  # E.g. v0.1.1 should not be before v0.1.10
  versions <- c(
    output,
    rev(other_versions[order(
      nchar(other_versions),
      other_versions
    )])
  )

  print(paste0("Version order in drop-down: ", versions))

  # Construct the text for each version based on the configuration
  text <- sapply(
    versions,
    FUN = function(x) {
      text <- conf$config$text[[x]]
      if (is.null(text)) {
        x
      } else {
        text
      }
    },
    simplify = TRUE
  )

  # Construct the tooltip for each version based on the configuration
  tooltip <- sapply(
    versions,
    FUN = function(x) {
      text <- conf$config$tooltip[[x]]
      if (is.null(text)) {
        ""
      } else {
        text
      }
    },
    simplify = TRUE
  )

  # Construct the HTML for each version in the dropdown menu
  menu_items <- paste0(
    '<a class="dropdown-item" data-toggle="tooltip" title="',
    tooltip,
    '" href="',
    base_url,
    "/",
    versions,
    '">',
    text,
    "</a>",
    collapse = "\n"
  )

  # Construct the complete HTML for the dropdown menu
  button <- paste(
    paste(
      start_tag,
      '<li class="nav-item dropdown">
        <a href="#" class="nav-link dropdown-toggle"
          data-bs-toggle="dropdown" role="button"
          aria-expanded="false" aria-haspopup="true"
          id="dropdown-versions">Versions</a>',
      collapse = "\n"
    ),
    '<div class="dropdown-menu" aria-labelledby="dropdown-versions">',
    menu_items,
    paste("</div></li>", end_tag, sep = "\n")
  )

  return(button)
}

# ------------------------------------------------------------
# Define a function to update content with the dropdown button
# ------------------------------------------------------------
update_content <- function(
    refs_to_list = paste(
      "^main$",
      "^devel$",
      "^pre-release$",
      "^latest-tag$",
      "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
      sep = "|"
    ),
    insert_after_section = "Changelog",
    refs_order = c(
      "devel",
      "pre-release",
      "main",
      "latest-tag"
    ),
    version_tab = "") {
  # Prepare the dropdown button based on the provided parameters
  dropdown_button <-
    prepare_dropdown_button(handle_missing_refs_list(refs_to_list), refs_order, version_tab)

  # List all HTML files in the current directory and its subdirectories
  html_files <- list.files(
    path = ".",
    pattern = ".html$",
    include.dirs = FALSE,
    recursive = TRUE,
    full.names = TRUE
  )

  # Iterate over each HTML file, updates the content by inserting the
  # dropdown button, and writes the updated content back to the file
  for (f in html_files) {
    # Read the contents of each HTML file into a vector
    html_content <- readLines(f)

    # Replace previous instances
    drowdown_start_line <-
      grep(pattern = start_tag, x = html_content)

    # Find the start and end lines of the dropdown button in the HTML content
    dropdown_end_line <- grep(pattern = end_tag, x = html_content)

    # Remove the previous dropdown button from the HTML content if it exists
    if (length(drowdown_start_line) > 0 &&
      length(dropdown_end_line) > 0) {
      html_content <-
        html_content[-(drowdown_start_line:dropdown_end_line)]
    }

    # Construct the string to search for in the HTML files to insert the dropdown button after
    insert_after <-
      paste0('index.html">', insert_after_section, "</a>")

    # Extract the package version from the string
    pkgdown_version <- "0.0.0"
    pkgdown_version_match <- grep("pkgdown</a> \\d+\\.\\d+\\.\\d+", html_content, value = TRUE)
    if (length(pkgdown_version_match) > 0) {
      pkgdown_version <- gsub(".*?(\\d+\\.\\d+\\.\\d+).*", "\\1", pkgdown_version_match)
    }

    # Adjust the insert line location based on the version of pkgdown
    if (compareVersion(pkgdown_version, "2.1.0") >= 0) {
      insert_after <- paste0(insert_after, "</li>")
    }

    # Find the line number where the dropdown button should be inserted
    insert_line <-
      grep(pattern = insert_after, x = html_content) + 1
    if (compareVersion(pkgdown_version, "2.1.0") >= 0) {
      insert_line <- insert_line - 1
    }

    # Check if the insert line is found
    if (length(insert_line) > 0) {
      # Insert the dropdown button into the HTML content
      html_content <- c(
        html_content[1:insert_line],
        dropdown_button,
        html_content[(insert_line + 1):length(html_content)]
      )
      # Write the updated HTML content back to the file
      writeLines(html_content, f)
    } else {
      # If the insert line is not found, print a message
      message(paste(
        f,
        ": Could not find the",
        insert_after,
        "tag"
      ))
    }
  }

  # Update the search indexes for each version
  update_search_indexes(refs_to_list)
}
