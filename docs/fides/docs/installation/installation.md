# Installation

This page describes installation options that you might use when considering how to install fidesctl. Fidesctl consists of multiple components, possibly distributed among various physical or virtual machines. Therefore installation of fidesctl might be complex, depending on the options you choose.

You should also check-out the [Prerequisites](prerequisites.md) that must be fulfilled when installing fidesctl. Fidesctl requires additional [Dependencies](dependencies.md) to be installed - which can be done via `extras`.

When you install fidesctl, you need to [setup the database](database.md) which must also be kept updated when fidesctl is upgraded.

## Using PyPI

More details: [Installation from PyPI](pypi.md)

### **When this option works best**

* This installation method is useful when you are not familiar with Containers and Docker. and want to install fidesctl on physical or virtual machines and you are used to installing and running software using custom deployment mechanism.
* The only officially supported mechanism of installation is via pip.

### **Intended users**

* Users who are familiar with installing and configuring Python applications, managing Python environments, dependencies and running software with their custom deployment mechanisms.

### **What are you expected to handle**

* You are expected to install fidesctl - all components of it - on your own.
* You should develop and handle the deployment for all components of fidesctl.
* You are responsible for setting up the database, automated startup and recovery, maintenance, cleanup and upgrades of fidesctl.

### **What the Fidesctl community provides for this method**

* You have [Installation from PyPI](pypi.md) on how to install the software but due to various environments and tools you might want to use, you might expect that there will be problems which are specific to your deployment and environment that you will have to diagnose and solve.
* You have [Running fidesctl locally](../quickstart/local.md) where you can see an example of Quick Start with running fidesctl locally. You can use this guide to start fidesctl quickly for local testing and development. However this is just an inspiration.

### **Where to ask for help**

* The #troubleshooting channel on the fidesctl Slack for quick general troubleshooting questions. The [GitHub discussions](https://github.com/ethyca/fides/discussions) if you look for longer discussion and have more information to share.
* If you can provide description of a reproducible problem with the fidesctl software, you can open issue in [GitHub issues](https://github.com/ethyca/fides/issues).

## Using Production Docker Images
