# get &mdash; print information about a single resource


### SYNOPSIS


**fidesctl get _resource_type_ _fides_key_**


### DESCRIPTION


The `get` command prints a JSON object that describes the resource object identified by the arguments.

### ARGUMENTS

***resource_type***


The type of resource that you want to retrieve, one of the following:

* `data_category`
* `data_qualifier`
* `data_subject`
* `data_use`
* `dataset`
* `organization`
* `policy`
* `registry`
* `system`

***fides_key***

The fides key that uniquely identifies the resource that you want to retrieve. The key is given as the `fides_key` property in the manifest file that defines the resource. To print the resource objects (and their `fides_key`s) to the terminal, call `fidesctl&nbsp;ls&nbsp;_resource_type_`.

### OPTIONS

**-h/--help**

Prints a synopsis of this command.





