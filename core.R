#!/usr/bin/env Rscript

start_tag <- "<!-- start dropdown for versions -->"
end_tag <- "<!-- end dropdown for versions -->"

prepare_dropdown_button <- function(refs_to_list = paste(
                                      "^main$",
                                      "^devel$",
                                      "^pre-release$",
                                      "^latest-tag$",
                                      "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                                      sep = "|"
                                    ), versions_dropdownlist_config="") {

  conf <- eval(parse(text=versions_dropdownlist_config))

  # List and sort versions
  versions <- sort(list.dirs(
    path = ".",
    recursive = FALSE,
    full.names = FALSE
  ), decreasing = TRUE)
  versions <- versions[grep(refs_to_list, versions)]
  # E.g. v0.1.1 should not be before v0.1.10
  versions <- rev(versions[order(nchar(versions), versions)])

  text <- sapply(versions, FUN = function(x){
    text <- conf$config$text[[x]]
    if(is.null(text)) x else text
  }, simplify = TRUE)

  tooltip <- sapply(versions, FUN = function(x){
    text <- conf$config$tooltip[[x]] 
    if(is.null(text)) "" else text
  }, simplify = TRUE)

  menu_items <- paste0(
    '<a class="dropdown-item" data-toggle="tooltip" title="',
    tooltip,
    '" href="https://',
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

update_content <- function(refs_to_list = paste(
                             "^main$",
                             "^devel$",
                             "^pre-release$",
                             "^latest-tag$",
                             "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
                             sep = "|"
                           ),
                           insert_after_section = "Changelog",
                           versions_dropdownlist_configuration = "") {
  dropdown_button <- prepare_dropdown_button(refs_to_list, versions_dropdownlist_configuration)

  html_files <- list.files(
    path = ".",
    pattern = ".html$",
    include.dirs = FALSE,
    recursive = TRUE,
    full.names = TRUE
  )

  insert_after <- paste0('index.html">', insert_after_section, "</a>")

  for (f in html_files) {
    html_content <- readLines(f)
    # Replace previous instances
    drowdown_start_line <- grep(
      pattern = start_tag, x = html_content
    )
    dropdown_end_line <- grep(
      pattern = end_tag, x = html_content
    )
    if (length(drowdown_start_line) > 0 && length(dropdown_end_line) > 0) {
      html_content <- html_content[- (drowdown_start_line:dropdown_end_line)]
    }
    insert_line <- grep(pattern = insert_after, x = html_content) + 1
    if (length(insert_line > 0)) {
      html_content <- c(
        html_content[1:insert_line],
        dropdown_button,
        html_content[(insert_line + 1):length(html_content)]
      )
      writeLines(html_content, f)
    } else {
      message(
        paste(
          f,
          ": Could not find the",
          insert_after,
          "tag"
        )
      )
    }
  }
}
