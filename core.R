#!/usr/bin/env Rscript

start_tag <- "<!-- start dropdown for versions -->"
end_tag <- "<!-- end dropdown for versions -->"
add_links_pattern <- '<ul class="navbar-nav me-auto">'

prepare_dropdown_button <- function(refs_to_list = paste(
                                      "^main$",
                                      "^devel$",
                                      "^pre-release$",
                                      "^latest-tag$",
                                      "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                                      sep = "|"
                                    )) {
  # List and sort versions
  versions <- sort(list.dirs(
    path = ".",
    recursive = FALSE,
    full.names = FALSE
  ), decreasing = TRUE)
  versions <- versions[grep(refs_to_list, versions)]
  # E.g. v0.1.1 should not be before v0.1.10
  versions <- rev(versions[order(nchar(versions), versions)])
  menu_items <- paste0(
    '<a class="dropdown-item" href="https://',
    Sys.getenv("GITHUB_REPOSITORY_OWNER"),
    ".github.io/",
    gsub(
      paste0(Sys.getenv("GITHUB_REPOSITORY_OWNER"), "/"),
      "",
      Sys.getenv("GITHUB_REPOSITORY")
    ),
    "/",
    versions,
    '">',
    versions,
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

update_content <- function(refs_to_list = paste(
                             "^main$",
                             "^devel$",
                             "^pre-release$",
                             "^latest-tag$",
                             "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                             sep = "|"
                           )) {
  dropdown_button <- prepare_dropdown_button(refs_to_list)

  html_files <- list.files(
    path = ".",
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
    start_line <- grep(pattern = add_links_pattern, x = html_content) + 1
    if (length(start_line > 0)) {
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
