<div id="cli-docs" class="cli">
  <h1>ls</h1>

  <div class="label">NAME</div>

  <div class="content">
    <span class="mono">ls</span> &mdash; print information about all the resources of a specific type
  </div>

  <div class="label">SYNOPSIS</div>

  <div class="content">
    <pre><code>fidesctl ls <i>resource_type</i></code></pre>
  </div>

  <div class="label">DESCRIPTION</div>

  <div class="content">
    The <code>ls</code> command prints a series of JSON objects that describe the <i>resource_type</i> resource objects that are defined by your system. 
  </div>
  <div class="label">ARGUMENTS</div>
  <div class="content">
    <div class="monoi">
      resource_type
    </div>
    <div class="content">
      The type of resources that you want to retrieve, one of the following:
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


