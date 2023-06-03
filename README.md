# commonplace

## Setup

This project uses [Poetry] for environment and dependency management.

To get started, [install Poetry](https://python-poetry.org/docs/#installation) and then run:

```shell
poetry install
```

To get a virtual environment:

```shell
poetry shell
```

## Running locally

You'll need to run [EdgeDB] locally.
You can do this via the EdgeDB CLI or via Docker, see [EdgeDB's quick start](https://www.edgedb.com/docs/intro/quickstart) for more detailed info.

Run the migrations, which will also make sure you are properly connected to the EdgeDB instance:

```shell
edgedb migrate
```

If everything looks good, you can run the app, enabling debug mode:

```shell
export COMMONPLACE_DEBUG=True
poetry run uvicorn commonplace.app:app
```

The app will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

To populate some canned data, visit the `/make-data` endpoint ([http://127.0.0.1:8000/make-data](http://127.0.0.1:8000/make-data))

## Linting

This project uses [Black], [MyPy] and [Flake8].

### Black

```shell
black commonplace/ tests/
```

### MyPy

```shell
mypy commonplace/ tests/
```

### Flake8

```shell
flake8 commonplace/ tests/
```

[EdgeDB]: https://www.edgedb.com/
[Black]: https://black.readthedocs.io/en/stable/
[Flake8]: https://flake8.pycqa.org/en/latest/
[MyPy]: https://mypy-lang.org/
[Poetry]: https://python-poetry.org/
