## Codabench Documentation
Welcome to the Codabench Documentation.

You can access the documentation generated from this folder [here](https://codalab.org/codabench/latest/)

If you want to contribute to the docs, you can create a Pull Request modifying the files you want (located in `docs/`) while adding a quick explanation on what you have changed and why.


When creating a Pull Request to modify the core code of Codabench, you can also include the docs modification by modifying the relevant files. Once the Pull Request is merged, the docs will automatically be updated with your changes (`dev` tag when it's merged into develop, and the `latest` version of the docs once it's merged in master)

## How to build
To build the docs locally, you will have to first install [uv](https://github.com/astral-sh/uv)

Once that is done, you can run the following commands (while inside this folder):

```bash
uv sync # You only need to run this once, it will download all the necessary python packages
PDF=1 uv run mkdocs serve -a localhost:8888 # This will build the site and serve it on localhost:8888
```

Open [localhost:8888](http://localhost:8888/) in your browser and you will see the docs. Every changes you make will rebuild the documentation.
You can remove the `PDF=1` environement variable if you want to speed up the build process, but you will not generate the related PDF.


### Versioning
We use the [mike](https://github.com/jimporter/mike) plugin to preserve multiple version of the docs.

To use it, you can run the following command: 
```bash
PDF=1 uv run mike deploy -u dev # This will create the site and push the changes in the gh-pages branch
uv run mike serve -a localhost:8888 # Serve the site on localhost:8888
```
Check the official Github page of the plugin for more information on how it works.

## Images and Assets
Images and assets are saved in the `_attachments` folder closest to the documentation file that calls for the image. If an image is used in multiple different places, then it should be put in `_attachements` folder in the `docs/` root directory.

## Github workflow
We have Github workflows set up to automatically rebuild the docs when the `develop` branch receives changes, and when a new tag is created for the `master` branch.