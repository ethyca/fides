# fidesctl CLI Overview

---

`fidesctl` provides an interactive shell that drives the Fides functionality. It can be pip installed with `pip install fidesctl`, but some functionality will not work unless the API and database are also set up.

<div id="cli-docs" class="cli">
  <div class="label">OPTIONS</div>
  <div class="content">
    <div class="mono">
      -f/--config-path <i>config_file</i> 
    </div>
    <div class="content">
      Identifies a file that you can use to configure the <code>fidesctl</code> environment. For more information about the file, see <a href="configuration-file">fidesctl Configuration File</a>. To see the current configuration file, do <code>fidesctl&nbsp;view&#8209;config</code>.
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
    The <code>fidesctl</code> commands are listed below. Follow the links for more information.
    <ul>
      <li><a href="../apply"><code>apply</code></a> creates and updates resource objects by reading a set of resource manifest files.</li>
      <li><a href="../delete"><code>delete</code></a> deletes a resource.</li>
      <li><a href="../evaluate"><code>evaluate</code></a> runs your policies against your data and announces the results.</li>
      <li><a href="../get"><code>get</code></a> prints information about a resource.</li>
      <li><a href="../init-db"><code>init-db</code></a> initializes and launches your resource database.</li>
      <li><a href="../ls"><code>ls</code></a> lists the resources of a specific type.</li>
      <li><a href="../parse"><code>parse</code></a> validates the taxonomy built from a set of resource manifest files.</li>
      <li><a href="../ping"><code>ping</code></a> determines if the fides API host is ready to receive messages.</li>
      <li><a href="../reset-db"><code>reset-db</code></a> removes the previously-applied manifest data from your resource database.</li>
      <li><a href="../view-config"><code>view-config</code></a> prints the <code>fidesctl</code> configuration settings as a JSON object.</li>
      <li><a href="../webserver"><code>webserver</code></a> starts the <code>fidesctl</code> API server.</li>
    </ul>
    <p>
  </div>
</div>
