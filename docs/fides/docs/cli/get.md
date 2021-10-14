<h1>get</h1>

<div class="label">NAME</div>

<div class="content">
  <span class="mono">get</span> &mdash; print information about a single resource
</div>

<div class="label">SYNOPSIS</div>

<div class="content">
  <pre><code>fidesctl get <i>resource_type</i> <i>fides_key</i>
  </div>

  <div class="label">DESCRIPTION</div>

  <div class="content">
    The <code>get</code> command prints a JSON object that describes the resource object identified by the arguments.
  </div>
  <div class="label">ARGUMENTS</div>
  <div class="content">
    <div class="monoi">
      resource_type
    </div>
    <div class="content">
      The type of resource that you want to retrieve, one of the following:
      <ul>
        <li><code>data_category</code></li>
        <li><code>data_qualifier</code></li>
        <li><code>data_subject</code></li>
        <li><code>data_use</code></li>
        <li><code>dataset</code></li>
        <li><code>organization</code></li>
        <li><code>policy</code></li>
        <li><code>registry</code></li>
        <li><code>system</code></li>
      </ul>
    </div>
  </div>
  <div class="content">
    <div class="monoi">
      fides_key
    </div>
    <div class="content">
    <div class="content">
      The fides key of the resource that you want to retrieve. The key is a string token that uniquely identifies the policy. You can find the key by looking in the policy manifest file, or by calling <code>fidesctl get policy</code>. The <code>fides-key</code> property specifies a policy's fides key value.
    </div>
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
      Prints a synopsis of this command with a list of options.
    </div>
  </div>
</div>


