<div id="cli-docs" class="cli">
  <h1>evaluate</h1>

  <div class="label">NAME</div>
  <div class="content">
    <span class="mono">evaluate</span> &mdash; run your privacy policies against your data
  </div>

  <div class="label">SYNOPSIS</div>
  <div class="content">
    <pre><code>fidesctl evaluate <i>manifest_dir</i> [-k/--fides-key <i>key</i>] [-m/--message <i>message</i>] [--dry]</code></pre>
  </div>

  <div class="label">DESCRIPTION</div>

  <div class="content">
    The <code>evaluate</code> command applies the resources defined in <i>manifest_dir</i> to your server (by calling <a href="/cli/apply/"><code>apply</code></a>), and then assesses your data's compliance to your policies. A failure means that you're trying to publish data that shouldn't be published; it's expected that you'll correct the data (or adjust the policy) before your next app deployment.
    <p>If you want to evaluate a single policy, use the <code>&#8209;&#8209;fides&#8209;key</code> option, passing the fides key of the policy you wish to evaluate.
    </p>
    <p>
      Keep in mind that <code>evaluate</code> calls <code>apply</code> for you; you don't have to call it yourself before you call this command.
    </p>
  </div>
  <div class="label">ARGUMENTS</div>

  <div class="content">
    <div class="monoi">
      manifest_dir 
    </div>
    <div class="content">
      The root of a directory tree that contains the resource manifest files that you want to apply to the server. The directories in the tree may <em>only</em> contain valid YAML files that describe Fides resources. If you include any other file, the command will fail and the valid resources will be ignored.
    </div>
  </div>
  <div class="label">OPTIONS</div>
  <div class="content">
    <div class="mono">
      -k/--fides-key <i>key</i>
    </div>
    <div class="content">
      The fides key of the single policy that you wish to evaluate. The key is a string token that uniquely identifies the policy. A policy's fides key is given as the <code>fides&#8209;key</code> property in the manifest file that defines the policy resource. To print the policy resources to the terminal, call  <code>fidesctl&nbsp;ls&nbsp;policy</code>. 
    </div>
  </div>
  <div class="content">
    <div class="mono">
      -m/--message <i>message</i>
    </div>
    <div class="content">
      A message that you can supply to describe the purpose of this evaluation. 
    </div>
  </div>
  <div class="content">
    <div class="mono">
      --dry 
    </div>
    <div class="content">
      "Dry run" mode. As it applies the resource manifest files, the command prints out the number of resources it would create, update, and delete, but it doesn't actually apply the changes to your server.
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

