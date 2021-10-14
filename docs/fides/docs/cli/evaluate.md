<div class="cli">
  <h1>evaluate</h1>
  <span class="label">NAME</span>

  <div class="content">
    <span class="mono">evaluate</span> &mdash; run your privacy policies against your data
  </div>

  <span class="label">SYNOPSIS</span>

  <div class="content">
    <pre><code>fidesctl evaluate <i>manifest_dir</i> [-k/--fides-key <i>key</i>] [-m/--message <i>message</i>] [--dry]</code></pre>
  </div>

  <span class="label">DESCRIPTION</span>

  <div class="content">
    The <code>evaluate</code> command applies the resources defined in <i>manifest_dir</i> to your server (by calling <a href="apply"><code>apply</code></a>), and then assesses your data's compliance to your policies. A failure means that you're trying to publish data that shouldn't be published; it's expected that you'll correct the data (or adjust the policy) before your next app deployment.
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
      The root of a directory tree that contains the resource manifest files that you want to apply to the server. The directories in the tree may <em>only</em> contain valid YAML files that describe Fides resources. If you include any other file, the command will throw an error. <span class="comment">The command crashes if you include non-manifest files. This seems a bit harsh -- is it a bug?</span>
    </div>
  </div>
  <div class="label">OPTIONS</div>
  <div class="content">
    <div class="mono">
      -k/--fides-key <i>key</i>
    </div>
    <div class="content">
      The fides key of the single policy that you wish to evaluate. The key is a string token that uniquely identifies the policy. You can find the key by looking in the policy manifest file, or by calling <code>fidesctl get policy</code>. The <code>fides-key</code> property specifies a policy's fides key value.
    </div>
  </div>

  <div class="content">
    <div class="mono">
      -m/--message <i>message</i>
    </div>
    <div class="content">
      <span class="tag">Unimplemented</span> A message that describes the purpose of this evaluation. <span class="comment">The message is attached to the evaluate object, but I don't see any mechanism for retrieving it</span>
    </div>
  </div>
  <div class="content">
    <div class="mono">
      --dry 
    </div>
    <div class="content">
      "Dry run" mode. This option is applied when <code>evaluate</code> calls the <a href="apply"><code>apply</code></a> command, which see.
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

