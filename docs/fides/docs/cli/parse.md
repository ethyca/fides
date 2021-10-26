<div id="cli-docs" class="cli">
  <h1>parse</h1>

  <div class="label">NAME</div>

  <div class="content">
    <span class="mono">parse</span> &mdash; validate a taxonomy
  </div>

  <div class="label">SYNOPSIS</div>

  <div class="content">
    <pre><code>fidesctl parse <i>manifest_dir</i> [-v/--verbose]</code></pre>
  </div>

  <div class="label">DESCRIPTION</div>

  <div class="content">
    The <code>parse</code> command validates the taxonomy that's built from the resource manifest files that are stored in <code><i>manifest_dir</i></code> and its subdirectories. If the taxonomy is successfully validated, the command prints a success message and returns 0. If its invalid, the command prints one or more error messages and returns non-0. The taxonomy itself is displayed if you include the <code>&#8209;&#8209;verbose</code> option, otherwise it's built silently. 
    <p>
    The resources that make up the taxonomy aren't applied to your server. 
    </p>
  </div>

  <div class="label">ARGUMENTS</div>

  <div class="content">
    <div class="monoi">
      manifest_dir 
    </div>
    <div class="content">
      The root of a directory tree that contains the resource manifest files that will be used to build the taxonomy. 
    </div>
  </div>
  <div class="label">OPTIONS</div>

  <div class="content">
    <div class="mono">
      -v/--verbose
    </div>
    <div class="content">
      Prints the taxonomy.
    </div>
  </div>
    <div class="content">
    <div class="mono">
      -h/--help
    </div>
    <div class="content">
      Prints a synopsis of this command.
    </div>
  </div>
</div>
