# Code Style

---

## General

### Docstrings

Docstrings are required for every function, class and method. No specific style is required or encouraged, as we expect that most of the relevant information can be gleaned from both the function signature's type-hints as well as descriptive parameter names. The docstring should serve to give additional context/flavour beyond that which can be gained from the code itself.

```python title="Docstring Example"
# Bad
def execute_evaluation(taxonomy: Taxonomy) -> Evaluation:
    """
    Execute an evaluation. 
    """

# Good
def execute_evaluation(taxonomy: Taxonomy) -> Evaluation:
    """
    Check the stated constraints of each Privacy Policy's rules against
    each system's privacy declarations.
    """
```

### Variable/Parameter Naming

Variable and parameter names should be as self-describing as possible. Brevity is not a concern here. Here are some common examples for writing good self-documenting code:

```python title="Single Letter Variable Names"
# Incorrect
s = 726

# Correct
elapsed_time_seconds = 726

# Incorrect
for n in nodes:
    print(n)

# Correct
for node in nodes:
    print(node)
```

```python title="Abbreviated Variable Names"
# Incorrect
r = requests.get(url)

# Incorrect
resp = reqeusts.get(url)

# Correct
response = requests.get(url)
```

```python title="Type Ambiguous Variable Names"
# Incorrect
food = ["apple", "banana"] 

# Incorrect
foods = ["apple", "banana"] 

# Correct
# Use type annotations if the name is somewhat ambiguous
foods: List[str] = ["apple", "banana"] 

# Correct
# The type is contained in the name
foods_list = ["apple", "banana"] 

# Correct
# Both of the above styles
foods_list: List[str] = ["apple", "banana"] 
```

## Pre-Commit Hooks

Fidesctl includes a `.pre-commit-config.yaml` to facilitate running CI checks before pushing up to a PR. The `pre-commit` package is included in the `dev-requirements.txt`. Once that is installed, follow these steps to get up and running:

1. `pre-commit install` - This is a one-time setup step to create the git pre-commit hooks
2. `pre-commit run` - This step will run all of the pre-commit jobs. They should all pass.
3. These pre-commit hooks will run now for you automatically.

## CI Checks

CI checks are stored as targets within the Makefile, and can be run from the top-level `fides` directory with the following pattern:

```bash title="Pattern"
make <lowercased_name>
```

```bash title="Examples"
make black
make mypy
make xenon
```

### Black formatting

Fidesctl's code is formatted using the [black](https://github.com/ambv/black) style. This style is checked in a CI step, and merges to master are prevented if code does not conform.

A number of extensions are available for popular editors that will automatically apply black to your code.

### Pylint

Fidesctl's code is linted using [pylint](https://pylint.org/). Linter checks run as part of a CI step and merges to master are prevented if code does not conform.

### Mypy

Fidesctl's code is statically-typed using [mypy](http://mypy-lang.org/). Type checking is validated as a CI step, and merges to master are prevented if code does not pass type checks. As a general rule, mypy typing requires all function arguments and return values to be annotated.

### Xenon

Fidesctl's code is checked for its cyclomatic-complexity by Xenon. If a single logical piece of code is deemed too complex, then a CI step will fail, at which point the focus should be on breaking up said complex function/method/class.
