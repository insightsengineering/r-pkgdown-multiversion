#!/usr/bin/env Rscript

# Set vars and constants
start_tag <- "<!-- start dropdown for versions -->"
end_tag <- "<!-- end dropdown for versions -->"

repo_name <-
  gsub(
    paste0(Sys.getenv("GITHUB_REPOSITORY_OWNER"), "/"),
    "",
    Sys.getenv("GITHUB_REPOSITORY")
  )
base_url <- paste0(
  "https://",
  Sys.getenv("GITHUB_REPOSITORY_OWNER"),
  ".github.io/",
  repo_name
)
search_index_file <- "search.json"

handle_missing_refs_list <- function(refs_to_list) {
  if (refs_to_list == "") {
    return("^(?!\\.git$).+$")
  }
  return(refs_to_list)
}


filter_versions <- function(refs_to_list = paste(
                              "^main$",
                              "^devel$",
                              "^pre-release$",
                              "^latest-tag$",
                              "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                              sep = "|"
                            )) {
  # List and sort versions
  versions <- sort(
    list.dirs(
      path = ".",
      recursive = FALSE,
      full.names = FALSE
    ),
    decreasing = TRUE
  )

  # Filter versions according to refs_to_list
  return(versions[grep(handle_missing_refs_list(refs_to_list), versions)])
}

update_search_indexes <- function(refs_to_list = paste(
                                    "^main$",
                                    "^devel$",
                                    "^pre-release$",
                                    "^latest-tag$",
                                    "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                                    sep = "|"
                                  )) {
  # Filter versions according to refs_to_list
  versions <- filter_versions(handle_missing_refs_list(refs_to_list))

  oldwd <- getwd()
  for (version in versions) {
    # Navigate to the ref
    setwd(version)
    # Update the indexes
    if (file.exists(search_index_file)) {
      search_index <- readLines(search_index_file)
      updated_index <- gsub(
        paste0(base_url, "(?!/", version, ")"),
        paste0(base_url, "/", version),
        search_index,
        perl = TRUE
      )
      writeLines(updated_index, search_index_file)
    }
    # Reset working directory
    setwd(oldwd)
  }
}

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
  conf <- eval(parse(text = version_tab))

  # Filter versions according to refs_to_list
  versions <- filter_versions(handle_missing_refs_list(refs_to_list))
  output <- c()

  # Append versions to output vector according to
  # the order in refs_order
  for (ref in refs_order) {
    result <- versions[grep(ref, versions)]
    if (!identical(result, character(0))) {
      output <- c(output, result)
    }
  }

  other_versions <-
    versions[!grepl(
      paste0(refs_order, collapse = "|"),
      versions
    )]

  # Append versions other than ones in refs_order
  # at the bottom of drop-down list.
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
  # Generate element
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
  dropdown_button <-
    prepare_dropdown_button(handle_missing_refs_list(refs_to_list), refs_order, version_tab)

  html_files <- list.files(
    path = ".",
    pattern = ".html$",
    include.dirs = FALSE,
    recursive = TRUE,
    full.names = TRUE
  )

  insert_after <-
    paste0('index.html">', insert_after_section, "</a>")

  for (f in html_files) {
    html_content <- readLines(f)
    # Replace previous instances
    drowdown_start_line <-
      grep(pattern = start_tag, x = html_content)
    dropdown_end_line <- grep(pattern = end_tag, x = html_content)
    if (length(drowdown_start_line) > 0 &&
      length(dropdown_end_line) > 0) {
      html_content <-
        html_content[-(drowdown_start_line:dropdown_end_line)]
    }
    insert_line <-
      grep(pattern = insert_after, x = html_content) + 1
    if (length(insert_line > 0)) {
      html_content <- c(
        html_content[1:insert_line],
        dropdown_button,
        html_content[(insert_line + 1):length(html_content)]
      )
      writeLines(html_content, f)
    } else {
      message(paste(
        f,
        ": Could not find the",
        insert_after,
        "tag"
      ))
    }
  }
  update_search_indexes(refs_to_list)
}
