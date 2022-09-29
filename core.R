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
                                    ),
                                    refs_order = c(
                                      "devel"), # TODO fix
                                    version_tab="") {

  conf <- eval(parse(text=version_tab))

  # List and sort versions
  versions <- sort(list.dirs(
    path = ".",
    recursive = FALSE,
    full.names = FALSE
  ), decreasing = TRUE)

  print("refs_order")
  print(refs_order)
  versions <- versions[grep(refs_to_list, versions)]
  output <- c()
  for (ref in refs_order) {
    result <- versions[grep(ref, versions)]
    if (!identical(result, character(0))) {
      output <- c(output, result)
    }
  }
  print("output")
  print(output)
  semantic_versions <- versions[grepl(
    "^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$",
    versions
  )]
  print("semantic_versions")
  print(semantic_versions)
  # Sorting according to the number of characters:
  # E.g. v0.1.1 should not be before v0.1.10
  versions <- c(
    output,
    rev(semantic_versions[
      order(nchar(semantic_versions),
      semantic_versions)
    ])
  )

print("versions")
print(versions)

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
                           version_tab = "") {
  dropdown_button <- prepare_dropdown_button(refs_to_list, version_tab)

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
