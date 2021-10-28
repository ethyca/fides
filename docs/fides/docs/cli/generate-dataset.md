#  generate-dataset &mdash; import a database schema


###  SYNOPSIS

**fidesctl generate-dataset _connection_string_ _output_filename_**

###  DESCRIPTION

The `generate-dataset` command reads one more schemas from a database by executing the <code><i>connection_string</i></code> statement, transforms the schemas into Dataset resources, and writes the Datasets (as YAML) to <code><i>output_filename</i></code>. 


###  ARGUMENTS

***connection_string***

An SQLAlchemy-compatible statement that connects to your database and reads one more schemas.

***output_filename***

The name of the Dataset manifest file that the command will write. The value can be an absolute or relative path, and should include the `.yml` or `.yaml` extension.

###  OPTIONS


**-h/--help** 

Prints a synopsis of this command.

