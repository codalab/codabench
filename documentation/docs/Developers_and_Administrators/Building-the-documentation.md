# Building the Documentation Locally

The documentation is located in the `documentation/` folder of the [Codabench repository](https://github.com/codalab/codabench). It is built with [Zensical](https://zensical.org/), and the pages are Markdown files located in `documentation/docs/`.

## Requirements

Install [uv](https://github.com/astral-sh/uv), the Python package manager used to install the dependencies.

## Build and serve

From the `documentation/` folder, run:

```bash
uv sync --frozen  # Only needed once, installs the necessary Python packages
uv run zensical serve -a localhost:8888  # Builds the site and serves it on localhost:8888
```

Then open [localhost:8888](http://localhost:8888/) in your browser. The documentation is rebuilt automatically every time you save a change.

## Adding a page

1. Create a Markdown file in `documentation/docs/` (images go in the closest `_attachments/` folder).
2. Add it to the `nav` section of `documentation/zensical.toml` so it appears in the menu.

## Publishing

Changes to the documentation are deployed automatically once merged: on the `dev` version when merged into `develop`, and on the `latest` version when merged into `master`.
