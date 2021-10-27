# delete &mdash; delete a resource

### SYNOPSIS

**fidesctl delete _resource_type_ _fides_key_**

### DESCRIPTION

The `delete` command deletes the resource object identified by the arguments.


### ARGUMENTS

***resource_type***

The type of resource that you want to delete, one of the following:

* data_qualifier
* data_subject
* data_use
* dataset
* organization
* policy
* registry
* system

***fides_key***

The fides key that uniquely identifies the resource that you want to delete. The key is given as the `fides key` property in the manifest file that defines the resource. To print the resource objects to the terminal, call <code>fidesctl&nbsp;ls&nbsp;<i>resource_type</i></code>.

### OPTIONS

**-h/--help**

Prints a synopsis of this command.





