# parse &mdash; validate your taxonomy


### SYNOPSIS


**fidesctl parse _manifest_dir_ [-v/--verbose]**


### DESCRIPTION


The `parse` command validates the taxonomy that's built from the resource manifest files that are stored in <code><i>manifest_dir</i></code> and its subdirectories. If the taxonomy is successfully validated, the command prints a success message and returns 0. If it's invalid, the command prints one or more error messages and returns non-0. The taxonomy itself is displayed if you include the `--verbose` option, otherwise it's built silently. 

The resources that make up the taxonomy aren't applied to your server. 


### ARGUMENTS

***manifest_dir***

The root of a directory tree that contains the resource manifest files that will be used to build the taxonomy. 

### OPTIONS

**-v/--verbose**

Prints the taxonomy.

**-h/--help**

Prints a synopsis of this command.



