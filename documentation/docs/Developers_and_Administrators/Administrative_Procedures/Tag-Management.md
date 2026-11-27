# Tag Management

Codabench includes Django admin interfaces and management commands to manage competition categories and tags.

## Creating Tags via Django Admin

Superusers can create and edit categories and tags directly in the **Django Admin** interface:

1. Log in with a superuser account and open the Django Admin (`/admin/`).
2. Under **Competitions**:
    - **Tag categories:** Click `Add Tag category`, enter the category name, and click **Save**.
    - **Tags:** Click `Add Tag`, enter the tag name, select its parent category from the dropdown, and click **Save**.

## Initializing Default Tags

To populate the database with default tag categories (*Machine Learning Domain*, *Fields of Application*, *Conference*) and their associated tags:

```bash
docker compose exec django ./manage.py init_tags
```

!!! note
    For the complete list of default categories and tags populated by this command, see the [YAML Structure documentation](../../Organizers/Benchmark_Creation/Yaml-Structure.md#tags).

### Resetting Tags
To delete all existing tags and categories and recreate the default taxonomy:

```bash
docker compose exec django ./manage.py init_tags --reset
```

!!! warning
    Running `--reset` deletes all existing tags and categories, which also removes all assigned tags from existing competitions.

## Auto-Tagging Pre-existing Competitions

To automatically classify and tag untagged competitions in the database (using LLMs via Ollama and title-based regex matching), you can use the standalone [codabench-competition-tagger](https://github.com/Mindr0ide/codabench-competition-tagger) tool.

It runs as a 3-step pipeline using JSON files, so inference can be executed on a separate machine (ideally with a GPU):

1. **Export** untagged competitions and the instance's active taxonomy from the Codabench database to a JSON file:

    ```bash
    docker compose exec django python export.py -o output/competitions_to_tag.json
    ```

2. **Predict** tags on your inference machine (ideally with a GPU) using the Ollama model specified in the command, the path to the input file (the one generated in the previous step), and `taxonomy.json` (keep `taxonomy.py` and `taxonomy.json` in the same directory as `predict.py`, or pass a custom path with `--taxonomy <path>`) This will generate a JSON file with the predicted tags on the specified output path:

    ```bash
    ollama pull qwen2.5:14b
    python3 predict.py -i output/competitions_to_tag.json -o output/predicted_tags.json -m qwen2.5:14b --workers 1
    ```

3. **Import** the predicted tags back into the database (you can preview the changes first with `--dry-run`). The input file is the one generated in the previous step:

    ```bash
    docker compose exec django python import_tags.py -i output/predicted_tags.json
    ```

!!! note
    Make sure your taxonomy tags are initialized in the database (via `./manage.py init_tags` or Django Admin) before importing, as `import_tags.py` strictly validates all tags against existing database entries.

For installation instructions, custom taxonomy configuration, and script options, see the [codabench-competition-tagger repository](https://github.com/Mindr0ide/codabench-competition-tagger).
