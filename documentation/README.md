## Codabench Documentation
Welcome to the Codabench Documentation.

You can access the documentation generated from this folder [here](https://codalab.org/codabench/latest/)

If you want to contribute to the docs, you can create a Pull Request modifying the files you want (located in `docs/`) while adding a quick explanation on what you have changed and why.


When creating a Pull Request to modify the core code of Codabench, you can also include the docs modification by modifying the relevant files. Once the Pull Request is merged, the docs will automatically be updated with your changes (`dev` tag when it's merged into develop, and the `latest` version of the docs once it's merged in master)

## How to build
To build the docs locally, you will have to first install [uv](https://github.com/astral-sh/uv)

Once that is done, you can run the following commands (while inside this folder):

```bash
uv sync --frozen # You only need to run this once, it will download all the necessary python packages
uv run zensical serve -a localhost:8888 # This will build the site and serve it on localhost:8888
```

Open [localhost:8888](http://localhost:8888/) in your browser and you will see the docs. Every changes you make will rebuild the documentation.
You can remove the `PDF=1` environement variable if you want to speed up the build process, but you will not generate the related PDF.

## Images and Assets
Images and assets are saved in the `_attachments` folder closest to the documentation file that calls for the image. If an image is used in multiple different places, then it should be put in `_attachements` folder in the `docs/` root directory.