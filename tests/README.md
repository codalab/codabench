# To tests locally
Install uv : https://docs.astral.sh/uv/getting-started/installation/

Run the following commands: 
```bash
uv sync
uv run pytest test_auth.py test_account_creation.py test_competition.py test_submission.py
```