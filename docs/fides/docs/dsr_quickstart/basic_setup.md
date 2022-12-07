# Get Started with DSR Automation

This guide is designed to walk you through configuring Fides and automating your first Data Subject Request.

To quickly run Fides against real databases for experimentation, see the provided [sample project](../getting-started/sample_project.md). 

## Set up a compute instance
The instance you use for running Fides should simulate a "typical" developer machine (e.g., a modern laptop with 8GB RAM, an m6g.large on AWS EC2, etc).

### Instance requirements
Your instance must: 

* Have [Docker](https://www.docker.com/products/docker-desktop) (version 20.10.11 or later) or [Python](https://www.python.org/downloads/) (version 3.8, 3.9, or 3.10) installed
* Have a hard drive to persist database volumes, YAML resource files, etc.
* Be accessible for interactive shell commands (e.g. SSH)
* Be accessible via HTTP for web browser commands

### Verify the installation

**For Docker installations,** run `docker -v` in a new shell to confirm that docker is ready to use:

```title="Example output:"
% docker -v
Docker version 20.10.11, build dea9396
```


**For Python installations,** run `python -version` in a new shell to confirm that docker is ready to use:

```title="Example output:"
% python --version
Python 3.9.13
```

## Next steps
You are now ready to install Fides, and set up your [environment](./environment_configuration.md)!