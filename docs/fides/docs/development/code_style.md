# Code Style

---

## General

### Docstrings

Docstrings are required for every function, class and method. No specific style is required or encourage, as we expect that most of the relevant information can be gleaned from both the function signature's type-hints as well as descriptive parameter names.

### Variable/Parameter Naming

Variable and parameter names should be as self-describing as possible. Brevity is not a concern here. Here are some common examples for writing good self-documenting code:

```python title="Single Letter Variable Names"
# Incorrect
for k, v in example_dict.items():
    print(k)
    print(v)

# Correct
for key, value in example_dict.items():
    print(key)
    print(value)
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

# More Correct
# Use type annotations if the name is somewhat ambiguous
foods: List[str] = ["apple", "banana"] 

# Most Correct
# The type is contained in the name
foods_list = ["apple", "banana"] 
```

## CI Checks

### Black formatting

Fidesctl's code is formatted using the [black](https://github.com/ambv/black) style. This style is checked in a CI step, and merges to master are prevented if code does not conform.

To apply black to your code, run black from the root Fidesctl directory:

```bash
cd fidesctl
black .
```

A number of extensions are available for popular editors that will automatically apply black to your code.

### Pylint

Fidesctl's code is linted using [pylint](https://pylint.org/). Linter checks run as part of a CI step and merges to master are prevented if code does not conform.

To apply pylint to your code, run pylint from the root Fidesctl directory:

```bash
cd fidesctl
pylint src
```

### Mypy typing

Fidesctl's code is statically-typed using [mypy](http://mypy-lang.org/). Type checking is validated as a CI step, and merges to master are prevented if code does not pass type checks. As a general rule, mypy typing requires all function arguments and return values to be annotated.

```bash
cd fidesctl
mypy src
```

### Xenon

Fidesctl's code is checked for its cyclomatic-complexity by Xenon. If a single logical piece of code is deemed too complex, then a CI step will fail, at which point the focus should be on breaking up said complex function/method/class.
