!!! note "This intervention is needed when upgrading from a version lower than [v1.26.0](https://github.com/codalab/codabench/releases/tag/v1.26.0)"

Emails sent by Codabench (sign-up confirmation, password reset, notifications, etc.) now use `DEFAULT_FROM_EMAIL` as sender address, instead of `SERVER_EMAIL`. Before starting the service, add `DEFAULT_FROM_EMAIL` to your `.env` file, with the address you had in `SERVER_EMAIL`:

```ini title=".env"
DEFAULT_FROM_EMAIL="Codabench <noreply@yourdomain.com>"
SERVER_EMAIL=noreply@yourdomain.com
```

You can keep `SERVER_EMAIL`: it is still used as sender address of the error emails sent by Django. If `DEFAULT_FROM_EMAIL` is not set, emails are sent from `Codabench <noreply@codabench.org>`, which your email server may refuse.

More information [here](https://github.com/codalab/codabench/pull/2271)
