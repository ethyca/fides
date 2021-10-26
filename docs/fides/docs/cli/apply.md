#  apply &mdash; create or update your resources


###  SYNOPSIS

**fidesctl apply _manifest_dir_ [--dry] [--diff]**

###  DESCRIPTION

The `apply` command reads the resource manifest files that are stored in <code><i>manifest_dir</i></code> and its subdirectories, and applies the resources to your server. If a named resource already exists, the resource is completely overwritten with the new description; if it doesn't exist, it's created.

As it processes the manifests, the command announces how many resources it has created, updated, and deleted.


###  ARGUMENTS

***manifest_dir***

The root of a directory tree that contains the resource manifest files that you want to apply to the server. The directories in the tree may _only_ contain valid YAML files that describe Fides resources. If you include any other file, the command will fail and the valid resource manifests will be ignored. 


###  OPTIONS

**--diff**

In addition to printing the number of changed resources, the command prints a diff between the server's old and new states. The diff is in <a href="https://pypi.org/project/deepdiff/" target="_blank">Python DeepDiff</a> format. 

**--dry** 

"Dry run" mode. As it applies the resource manifest files, `apply` prints out the number of resources it would create, update, and delete, but it doesn't actually apply the changes to your server.

**-h/--help** 

Prints a synopsis of this command.

