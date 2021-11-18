# r-pkgdown-multisite

Github Action to generate multiple versions of pkgdown docs for R packages.
Example of usage:

```yaml
---
name: Docs

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  pkgdown:
    name: Pkgdown Docs
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/insightsengineering/rstudio_4.1.0_bioc_3.13:latest
    steps:
      - name: Install R package
        run: R CMD INSTALL ${{ github.event.repository.name }}
        shell: bash

      - name: Build docs
        run: |
          options(repos = c(CRAN = "https://cloud.r-project.org/"))
          "pkgdown" %in% installed.packages() || install.packages("pkgdown", upgrade = "never")
          pkgdown::build_site("${{ github.event.repository.name }}", devel = TRUE)
        shell: Rscript {0}

      - name: Create artifacts
        run: |
          pushd ${{ github.event.repository.name }}/docs/
          zip -r9 $OLDPWD/pkgdown.zip *
          popd
        shell: bash

      - name: Upload docs for review
        if: github.ref != 'refs/heads/main'
        uses: actions/upload-artifact@v2
        with:
          name: pkgdown.zip
          path: pkgdown.zip

      - name: Publish docs
        if: github.ref == 'refs/heads/main' # Only after merge or push to main
        run: |
          cd ${{ github.event.repository.name }}
          git config --local user.email "actions@github.com"
          git config --local user.name "GitHub Actions"
          Rscript -e 'pkgdown::deploy_to_branch(new_process = FALSE)'
          
      - name: Change branch multisite docs
        uses: actions/checkout@v2
        with:
          ref: gh-pages

upload-release-assets: #upload tags
    name: Upload documentation assets
    needs: pkgdown
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
      - name: Checkout
        uses: actions/checkout@v2
      - name: Wait for release to succeed
        timeout-minutes: 2
        uses: lewagon/wait-on-check-action@v1.1.1
        with:
          ref: "${{ github.ref }}"
          check-name: 'Release'
          repo-token: ${{ secrets.REPO_GITHUB_TOKEN }}
          wait-interval: 10
      - name: Download artifact
        uses: actions/download-artifact@v2
        with:
          name: pkgdown.zip
      - name: Upload binaries to release
        uses: svenstaro/upload-release-action@v2
        with:
          repo_token: ${{ secrets.REPO_GITHUB_TOKEN }}
          file: pkgdown.zip
          asset_name: pkgdown.zip
          tag: ${{ github.ref }}
          overwrite: false
  
  multisite:
    name: Multisite creation
    if: ${{ (github.event_name == 'push' && github.ref == 'refs/heads/main') || startsWith(github.ref, 'refs/tags/v') }} # Only after merge or push to main or started on tags
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/insightsengineering/rstudio_4.1.0_bioc_3.13:latest
    needs: pkgdown
    steps:
      - name: Change branch multisite docs
        uses: actions/checkout@v2
        with:
          ref: gh-pages

      - name: Multisite docs update links 
        uses: insightsengineering/r-pkgdown-multisite@main
        env:
          GITHUB_PAT: ${{ secrets.REPO_GITHUB_TOKEN }}
      
      - name: Setup github user
        uses: fregante/setup-git-user@v1

      - name: Push changes, if any
        uses: EndBug/add-and-commit@v7

```
