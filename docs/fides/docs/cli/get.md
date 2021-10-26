<div class="cli">

  <h1>get</h1>

  <div class="label">NAME</div>

  <div class="content">
    <span class="mono">get</span> &mdash; print information about a single resource
  </div>

  <div class="label">SYNOPSIS</div>

  <div class="content">
    <pre><code>fidesctl get <i>resource_type</i> <i>fides_key</i></code></pre>
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
        The fides key that uniquely identifies the resource that you want to retrieve. The key is given as the <code>fides&#8209;key</code> property in the manifest file that defines the resource. To print the resource objects to the terminal, call <code>fidesctl&nbsp;ls&nbsp;<i>resource_type</i></code>.
      </div>
    </div>
  </div>
  
  <div class="label">OPTIONS</div>
  <div class="content">
    <div class="mono">
      -h/--help
    </div>
    <div class="content">
      Prints a synopsis of this command.
    </div>
  </div>
</div>


