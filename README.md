# MultiVersion pkgdown docs action

Github Action to generate multiple versions of [`pkgdown`](https://pkgdown.r-lib.org/) docs for R packages.

This Github Actions works under the following assumptions:

* R package documentation is generated by the R function [`pkgdown::build_site`](https://pkgdown.r-lib.org/reference/build_site.html)
* Documentation is published to the `gh-pages` branch of the package repository and Github Pages is enabled at the root level of the branch
* The version of `pkgdown` used to generate the documentation is `>= v2.0.0`
* The `pkgdown` documentation uses Bootstrap 5

An example of the output of the action can be seen below:

![Screenshot with example output](example.png)

## Action type

Composite

## Inputs

* `path`:

    _Description_: Path to package's root

    _Required_: `false`

    _Default_: `.`

* `default-landing-page`:

    _Description_: The default branch or tag on gh-pages that corresponds to the landing page. For instance, if your root index page on gh-pages is built using the 'main' branch, then the root page of the website will correspond to this page. If 'latest-tag' is selected, then the latest version will become the default.

    _Required_: `false`

    _Default_: `main`

* `branches-or-tags-to-list`:

    _Description_: Which branches or tags should be listed under the 'Versions' dropdown menu on the landing page? This input should be a regular expression in R.

    _Required_: `false`

    _Default_: `^main$|^devel$|^pre-release$|^latest-tag$|^develop$|^v([0-9]+\\.)?([0-9]+\\.)?([0-9]+)$`

* `insert-after-section`:

  _Description_: After which section in the navbar should the 'Versions' dropdown be added? Choose between 'Reference' and 'Changelog' for the surest of choices.

  _Required_: `false`

  _Default_: `Changelog`

* `version-tab`:

  _Description_: Configuration of how the drop-down list should appear for multiple versions. It should be set as an ASCII text representation of an R list object. Example:
    ```
        list(config = list(
                tooltip = list(
                    main = "Tooltip for main branch"
                ),
                text = list(
                    main = "main branch"
                )
                ))
    ```
    String should be quoted with " sign

  _Required_: `false`

  _Default_: ``



## Outputs

None.

## Usage

Please refer to [this example](https://github.com/insightsengineering/r.pkg.template/blob/main/.github/workflows/pkgdown.yaml) workflow to see how this action is used in an end-to-end documentation publishing workflow.
