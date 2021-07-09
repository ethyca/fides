# Code Style

---

## Black formatting

Fides's code is formatted using the [black](https://github.com/ambv/black) style. This style is checked in a CI step, and merges to master are prevented if code does not conform.

To apply black to your code, run black from the root Fidesctl directory:

```bash
cd fidesctl
black .
```

A number of extensions are available for popular editors that will automatically apply black to your code.

## Docstrings

Fides expects all functions to include docstrings.

## Pylint

Fides's code is linted using [pylint](https://pylint.org/). Linter checks run as part of a CI step and merges to master are prevented if code does not conform to a certain extent.

To apply pylint to your code, run pylint from the root Fidesctl directory:

```bash
cd fidesctl
pylint src
```

## Mypy typing

Fides's code is statically-typed using [mypy](http://mypy-lang.org/). Type checking is validated as a CI step, and merges to master are prevented if code does not pass type checks. As a general rule, mypy typing requires all function arguments and return values to be annotated.

```bash
cd fidesctl
mypy src
```
