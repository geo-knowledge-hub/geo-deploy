# GEO Knowledge Hub Deploy

`gkh deploy` provides tools to produce and verify GEO Knowledge Hub deployments.

## Install

`gkh deploy` is a plugin for the [`gkh`](https://github.com/geo-knowledge-hub/gkh-cli) command line, so you can install it with:

```bash
uv tool install --with gkh-deploy gkh-cli
```

## Usage

First, describe the instance:

```bash
gkh deploy init --hostname gkhub.example.org --admin-email you@example.org
```

This writes `gkh-deploy.yaml`, the only file you maintain. Open it and adjust the image tag, storage class and ingress class to your cluster.

Next, check it:

```bash
gkh deploy check
```

Nine rules run against the Helm values the configuration produces, each printing the chart template or upstream source that justifies it.

Then, render the bundle:

```bash
gkh deploy generate -o deploy/
```

You get `values.yaml`, `secrets.sh`, `bootstrap.sh`, a copy of the configuration, and a `README.md` carrying the `helm` commands for that bundle. Regenerate rather than editing these by hand.

Now you have these files generated, you can follow the `README.md` available in the `deploy/`.

> [!NOTE]
> No password appears anywhere in the bundle. The `secrets.sh` script generates them into Kubernetes Secrets and `values.yaml` refers to those, so credentials reach the pods through `secretKeyRef` rather than as literal environment values.

Then, once you have the instance up and running, you can execute the post-install commands. These commands are the same ones executed by the `bootstrap.sh`. If you want a more manual approach, you can take the post-install steps and execute them:

```bash
gkh deploy bootstrap
```

This command prints the steps to create a database, roles, administrator and vocabularies required by the GEO Knowledge Hub. Nothing is executed and no cluster is contacted. So, you can run them in the worker container yourself.

> [!NOTE]
> The manual approach is recommended for anyone setting up a production instance who needs to ensure that everything is controlled and behaves as expected.

## Validating an instance

`gkh validate` drives a running instance over its API and UI and reports what does not work well. It ships with `gkh deploy`, behind the `validation` extra:

```bash
uv tool install --with 'gkh-deploy[validation]' gkh-cli
```

Point it at an instance and run it:

```bash
gkh --url https://gkhub.example.org --token ... validate run
```

By default, `validate run` will run the entire test suite. To validate only a specific part of the instance, use the `--suite` flag. For example, to run only the UI:

```bash
gkh --url https://gkhub.example.org --token ... validate run --suite ui
```

For the API, the approach is the same:

```bash
gkh --url https://gkhub.example.org --token ... validate run --suite api
```

Please note that when you are testing the API, the tests has creation operations, including record publication, DOI minting, file upload and others. As these actions ca not be undone, they are skipped by default. To active them, you need to use the flag `--allow-publish` as presented below:

```bash
gkh --url https://gkhub.example.org --token ... validate run --allow-publish
```

Please note that it is possible to configure the instance, token and TLS using a `.env` file. You can create one by copying [`.env.example`](./.env.example) to `.env` and filling it in.

## Development

```bash
uv sync --extra validation
uv run pytest                                        # the CLI's own tests
uv run ruff check . && uv run ruff format --check .  # lint and format
```

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes, and ensure tests, linting and type checks pass before submitting a pull request.

## License

`gkh-deploy` is distributed under the MIT license. See [LICENSE](./LICENSE) for the full text.
