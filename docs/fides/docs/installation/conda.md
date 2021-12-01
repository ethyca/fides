# Installation from Conda

This page describes installations using the `fidesctl` package [published on Conda](https://anaconda.org/ethyca/fidesctl).

## Installation

To install Fidesctl, first create an environment with the fidesctl package and necessary channels:

```bash
conda create --name fidesctl-environment fidesctl \
             --channel ethyca \
             --channel plotly \
             --channel conda-forge
```

Then activate your environment to begin using the `fidesctl` cli:
`conda activate fidesctl-environment`
