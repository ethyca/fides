# reset-db &mdash; re-initialize your policy database

### SYNOPSIS

**fidesctl reset-db [-y/--yes]**

### DESCRIPTION

The `reset-db` command removes the resources that you added through previous `apply` calls and then re-initializes the database (through `init-db`).

### OPTIONS

**-y/--yes**

Before it removes the resources, `reset-db` prompts you to confirm the removal. This option suppresses the prompt; the resources are removed without your confirmation.

**-h/--help**

Prints a synopsis of this command.



