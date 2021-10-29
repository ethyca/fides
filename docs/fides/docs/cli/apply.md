<div id="cli-docs" class="cli">
  <h1>apply</h1>

  <div class="label">NAME</div>

  <div class="content">
    <span class="mono">apply</span> &mdash; create or update your resources
  </div>

  <div class="label">SYNOPSIS</div>

  <div class="content">
    <pre><code>fidesctl apply <i>manifest_dir</i> [--dry] [--diff]</code></pre>
  </div>

  <div class="label">DESCRIPTION</div>

  <div class="content">
    The <code>apply</code> command reads the resource manifest files that are stored in <code><i>manifest_dir</i></code> and its subdirectories, and applies the resources to your server. If a named resource already exists, the resource is completely overwritten with the new description; if it doesn't exist, it's created.
    <p>
      As it processes the manifests, the command announces how many resources it has created, updated, and deleted.
    </p>
  </div>

  <div class="label">ARGUMENTS</div>

  <div class="content">
    <div class="monoi">
      manifest_dir 
    </div>
    <div class="content">
      The root of a directory tree that contains the resource manifest files that you want to apply to the server. The directories in the tree may <em>only</em> contain valid YAML files that describe Fides resources. If you include any other file, the command will fail and the valid resource manifests will be ignored. 
    </div>
  </div>
  <div class="label">OPTIONS</div>

  <div class="content">
    <div class="mono">
      --diff 
    </div>
    <div class="content">
      In addition to printing the number of changed resources, the command prints a diff between the server's old and new states. The diff is in <a href="https://pypi.org/project/deepdiff/" target="_blank">Python DeepDiff</a> format. 
    </div>
  </div>

  <div class="content">
    <div class="mono">
      --dry
    </div>
    <div class="content">
      "Dry run" mode. As it applies the resource manifest files, <code>apply</code> prints out the number of resources it would create, update, and delete, but it doesn't actually apply the changes to your server.
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
