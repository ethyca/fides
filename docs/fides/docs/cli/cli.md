# fidesctl CLI Overview

---

`fidesctl` provides an interactive shell that drives the Fides functionality. If you run Fides in a  Docker container, you launch the `fidesctl` shell by `cd`ing to your `fides` root directory and running `make cli`.

```bash
$ cd <your-fides-root>
$ make cli
```

When it's finished,  `make cli` shows you a success message, `cd`s into the `fidesctl` directory, and presents you with the Docker prompt. Notice that the prompt includes your current working directory within the Docker container.

```bash
⠿ Container fides-fidesctl-db-1  Running   0.0s //success message
root@f76b4a7af333:/fides/fidesctl# //prompt
```

You can then use the `fidesctl` command line interface commands. The commands are provided as arguments to the `fidesctl` program. For example, to run the `init-db` command, you do this:

```bash
root@f76b4a7af333:/fides/fidesctl# fidesctl init-db
```

`fidesctl` itself takes a set of options. The most important option is `--config-path` which lets you supply a file that configures the `fidesctl` environment.
All `fidesctl` commands return 0 upon success.


<div class="cli">
  <div class="label">OPTIONS</div>

  <div class="content">
    <div class="mono">
      -f/--config-path <i>config_file</i> 
    </div>
    <div class="content">
      Identifies a file that you can use to configure the <code>fidesctl</code> environment. For more information about the file, see <a href="configuration-file">fidesctl Configuration File</a>.
    </div>
  </div>
  <div class="content">
    <div class="mono">
      -v/--version 
    </div>
    <div class="content">
      Prints the <code>fidesctl</code> version number.
    </div>
  </div>
  <div class="content">
    <div class="mono">
      -h/--help
    </div>
    <div class="content">
      Prints a synopsis of the <code>fidesctl</code> command. All of the `fidesctl` commands, listed below, also support the <code>-h</code>/<code>--help</code> options.
    </div>
  </div>

  <div class="label">COMMANDS</div>

  <div class="content">

    The <code>fidesctl</code> commands are listed below. Follow the link to the manual page for more information about a particular command.

    <ul>
    <li><a href="../apply"><code>apply</code></a> creates and updates resource objects by reading a set of resource manifest files.</li>
    <li><a href="../evaluate"><code>evaluate</code></a> runs your policies against your data and announces the results.</li>
    <li><a href="../get"><code>get</code></a> prints information about a single resource identified by type and key.</li>
    <li><a href="../init-db"><code>init-db</code></a> launches your resource database and initializes it with default resources definitions.</li>
    <li><a href="../ls"><code>ls</code></a> lists the resources of a specified type.</li>
    <li><a href="../ping"><code>ping</code></a> determines if the fides API host is ready to receive messages.* <a href="ping"><code>ping</code></a> determines if the fides API host is ready to receive messages.</li>
    <li><a href="../reset-db"><code>reset-db</code></a> removes the previously-applied manifest data from your resource database.</li>
    <li><a href="../view-config"><code>view-config</code></a> prints the <code>fidesctl</code> configuration settings as a JSON object.</li>
  </ul>
<p>
</div>
</div>
