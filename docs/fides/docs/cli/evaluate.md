# evaluate &mdash; execute and assess your privacy policies


### SYNOPSIS

**fidesctl evaluate _manifest_dir_ [-k/--fides-key _key_] [-m/--message _message_] [--dry]**

### DESCRIPTION


The `evaluate` command applies the resources defined in <code><i>manifest_dir</i></code> to your server (by calling `apply`), and then assesses your data's compliance to your policies. A failure means that you're trying to publish data that shouldn't be published; it's expected that you'll correct the data (or adjust the policy) before your next app deployment.

If you want to evaluate a single policy, use the `--fides-key` option, passing the fides key of the policy you wish to evaluate.

Keep in mind that since `evaluate` calls `apply` for you, you don't have to call it yourself before you call this command.

### ARGUMENTS

**manifest_dir**

The root of a directory tree that contains the resource manifest files that you want to apply to the server. The directories in the tree may _only_ contain valid YAML files that describe Fides resources. If you include any other file, the command will fail and the valid resources will be ignored.

### OPTIONS

**-k/--fides-key _key_**

The fides key of the single policy that you wish to evaluate. The key is a string token that uniquely identifies the policy. A policy's fides key is given as the `fides-key` property in the manifest file that defines the policy resource. To print the policy resources (and their `fides_key` values) to the terminal, call  `fidesctl&nbsp;ls&nbsp;policy`. 

**-m/--message _message_**

A message that you can supply to describe the purpose of this evaluation. 

**--dry**

"Dry run" mode. As it applies the resource manifest files, the command prints out the number of resources it would create, update, and delete, but it doesn't actually apply the changes to your server.

**-h/--help**

Prints a synopsis of this command.




