#!/usr/bin/env Rscript

start_tag <- "<!-- start dropdown for versions -->"
end_tag <- "<!-- end dropdown for versions -->"

prepare_dropdown_button <- function(docs_path = ".",
                                    refs_to_list = paste(
                                      "^main$",
                                      "^devel$",
                                      "^pre-release$",
                                      "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                                      sep = "|"
                                    )) {
  # List and sort versions
  versions <- sort(list.dirs(
    path = docs_path,
    recursive = FALSE,
    full.names = FALSE
  ), decreasing = TRUE)
  versions <- versions[grep(refs_to_list, versions)]
  # E.g. v0.1.1 should not be before v0.1.10
  versions <- rev(versions[order(nchar(versions), versions)])
  menu_items <- paste0(
    '<a class="dropdown-item" href="../',
    versions,
    '">',
    versions,
    "</a>",
    collapse = "\n"
  )
  # Generate element
  return(paste(
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
  ))
}

update_content <- function(docs_path = ".",
                           refs_to_list = paste(
                             "^main$",
                             "^devel$",
                             "^pre-release$",
                             "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                             sep = "|"
                           )) {
  dropdown_button <- prepare_dropdown_button(
    docs_path, refs_to_list
  )

  html_files <- dir(
    path = docs_path,
    pattern = ".html$",
    include.dirs = FALSE,
    recursive = TRUE,
    full.names = TRUE
  )

  for (f in html_files) {
    html_content <- readLines(f)
    # Replace previous instances
    start_release_line <- grep(
      pattern = start_tag,
      x = html_content
    )
    end_release_line <- grep(
      pattern = end_tag, x = html_content
    )
    if (length(start_release_line) > 0 && length(end_release_line) > 0) {
      html_content <- html_content[- (start_release_line:end_release_line)]
    }
    add_links_pattern <- '<ul class="navbar-nav me-auto">'
    start_line <- grep(pattern = add_links_pattern, x = html_content) + 1
    if (length(start_line == 1)) {
      html_content <- c(
        html_content[1:start_line],
        dropdown_button,
        html_content[(start_line + 1):length(html_content)]
      )
      writeLines(html_content, f)
    } else {
      message(
        paste(
          f,
          ": Could not find the",
          add_links_pattern,
          "tag"
        )
      )
    }
  }
}
