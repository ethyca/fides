# Quickstart 

With Fides you can enforce your organization's privacy policy in every pull request and merge. Learn the basics of working with Fide's CLI (`fidesctl`) locally with this quickstart guide.

## Prerequisites

1. Install `make`. We recommend installing `make` with these guides but you can use other resources.
  - For Mac, see [Homebrew's `make` formulae](https://formulae.brew.sh/formula/make)
  - For Windows, see this [`make` installation guide](http://gnuwin32.sourceforge.net/packages/make.htm)

2. Install a version of `docker` that includes support for `docker-compose`. We recommend installing [Docker Desktop](https://www.docker.com/products/docker-desktop) for Mac and Windows. For more information about Docker Compose, see "[Overview of Docker Compose](https://docs.docker.com/compose/)" on the Docker docs site.

## Step 1: Clone the [Fidesctl repo](https://github.com/ethyca/fides)

1. Clone the [Fidesctl repo](https://github.com/ethyca/fides).

```bash
$ git clone git@github.com:ethyca/fides.git                 
> Cloning into 'fides'...
> remote: Enumerating objects: 4855, done.
> remote: Counting objects: 100% (2485/2485), done.
> remote: Compressing objects: 100% (1095/1095), done.
> remote: Total 4855 (delta 1460), reused 1696 (delta 1071), pack-reused 2370
> Receiving objects: 100% (4855/4855), 14.66 MiB | 2.81 MiB/s, done.
> Resolving deltas: 100% (2620/2620), done.
```

2. Move into the `fides` directory, which contains the Makefile we want to work with.
```
$ cd fides
```

## Step 2: Start the `fidesctl` container to run `fidesctl` CLI

To build the interactive shell where you can run `fidesctl` CLI commands, run `make cli` from your fides directory. The first time you run `make cli` in your Fides repository, it may take around 3 minutes to build. 

You're ready to run `fidesctl` CLI commands once you see the `fidesctl#` prompt.

```bash
$ make cli
Build the images required in the docker-compose file...
...
Building fidesapi
...
Building fidesctl
...
Building docs
...
root@1a742083cedf:/fides/fidesctl#
```

## Step 3: Initialize `fidesctl` CLI

Now you're ready to build the required images, spin up the database, and run other initialization scripts with the `fidesctl init-db` command.

```bash
$ ~/fides/fidesctl# fidesctl init-db
> INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
> INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

## Step 4: Confirm your `fidesctl` CLI can reach the server

To confirm that `fidesctl` can reach the server and everything is ready to go, run `fidesctl ping`.

```bash
root@796cfde906f1:/fides/fidesctl# fidesctl ping
Pinging http://fidesctl:8080/health...
{
  "data": {
    "message": "Fides service is healthy!"
  }
}
```

## Step 5: Review the example files.

The fides repository you cloned includes a set of example files in the `fides/fidesctl/demo_resources` directory written in YAML and using the [Fides configuration syntax](/language/syntax/) and [Fides Taxonomy](/tutorial/taxonomy/).

These files represent your organization's privacy polcy, relevant data, registry, and system configuration. 

- `demo_dataset.yml` 
- `demo_policy.yml`
- `demo_registry.yml`
- `demo_system.yml`

To take a closer look at the privacy policy example, run `cat demo_resources/demo_policy.yml`. 

The `demo_policy.yml` has one rule: if any system uses contact information for marketing purposes, then a failure action will result.

```yaml
policy:
  - fides_key: demo_privacy_policy
    name: Demo Privacy Policy
    description: The main privacy policy for the organization.
    rules:
      - fides_key: reject_direct_marketing
        name: Reject Direct Marketing
        description: Disallow collecting any user contact info to use for marketing.
        data_categories:
          inclusion: ANY
          values:
            - user.provided.identifiable.contact
        data_uses:
          inclusion: ANY
          values:
            - advertising
        data_subjects:
          inclusion: ANY
          values:
            - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified
        action: REJECT
```

## Step 6: Test the privacy policy

To ensure that your systems are compliant with your privacy policy, you can run the `fidesctl evaluate` command. To check that the systems described in your `demo_system.yml` file do not use contact information for marketing purposes, run `fidesctl evaluate demo_resources/`.

```
root@fa175a43c077:/fides/fidesctl# fidesctl evaluate demo_resources
Loading resource manifests from: demo_resources
Taxonomy successfully created.
----------
Processing registry resources...
CREATED 1 registry resources.
UPDATED 0 registry resources.
SKIPPED 0 registry resources.
----------
Processing dataset resources...
CREATED 1 dataset resources.
UPDATED 0 dataset resources.
SKIPPED 0 dataset resources.
----------
Processing policy resources...
CREATED 1 policy resources.
UPDATED 0 policy resources.
SKIPPED 0 policy resources.
----------
Processing system resources...
CREATED 2 system resources.
UPDATED 0 system resources.
SKIPPED 0 system resources.
----------
Loading resource manifests from: demo_resources
Taxonomy successfully created.
Evaluating the following policies:
demo_privacy_policy
----------
Checking for missing resources...
Executing evaluations...
Sending the evaluation results to the server...
Evaluation passed!

```

## Step 7: Edit your systems files

To show you how `fidesctl` works when your systems would fail your privacy policy, let's modify the systems file that describes how the marketing system works.

In `demo_resources/demo_system.yml`, uncomment line 25, which will add `user.provided.identifiable.contact` to the list of `data_categories` for the `demo_marketing_system`.

```yaml
     privacy_declarations:
       - name: Collect data for marketing
         data_categories:
-          #- user.provided.identifiable.contact # uncomment to add this category to the system
+          - user.provided.identifiable.contact # uncomment to add this category to the system
           - user.derived.identifiable.device.cookie_id
         data_use: marketing_advertising_or_promotion
         data_subjects:
```

## Step 8: Evaulate the privacy policy again



