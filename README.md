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

Finally, once `helm install` has settled, run the post-install sequence:

```bash
gkh deploy bootstrap
```

This prints the seven steps that create the database, roles, administrator and vocabularies, with the `invenio` commands each one runs. Nothing is executed and no cluster is contacted. Run them in the worker container yourself, or use `deploy/bootstrap.sh`, which is the same sequence packaged as a script that finds the pod for you.

No password appears anywhere in the bundle. `secrets.sh` generates them into Kubernetes Secrets and `values.yaml` refers to those, so credentials reach the pods through `secretKeyRef` rather than as literal environment values.

## Validating an instance

`validation/` is a pytest suite that exercises a deployed instance over its API and UI:

```bash
uv run pytest validation/ -v
```

See [`validation/README.md`](validation/README.md) for configuration and for adding tests.

## Development

```bash
uv sync
uv run pytest                                        # the CLI's own tests
uv run ruff check . && uv run ruff format --check .  # lint and format

# render every bundle against the real chart. Needs helm in PATH
GKH_CHART_PATH=/path/to/helm-invenio/charts/invenio uv run pytest -m integration
```

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes, and ensure
tests, linting and type checks pass before submitting a pull request.

## License

`gkh-deploy` is distributed under the MIT license. See [LICENSE](./LICENSE) for the full text.
