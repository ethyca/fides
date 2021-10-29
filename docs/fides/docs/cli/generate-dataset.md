<div id="cli-docs" class="cli">
  <h1>generate-dataset</h1>

  <div class="label">NAME</div>
  <div class="content">
    <span class="mono">annotate-dataset</span> &mdash; guided dataset annotation
  </div>
  <div class="label">SYNOPSIS</div>
  <div class="content">
    <pre><code>fidesctl generate-dataset <i>connection_string</i> <i>output_filename</i></code></pre>
  </div>

  <div class="label">DESCRIPTION</div>
  <div class="content">
    The <code>generate-dataset</code>  command reads one more schemas from a database by executing the <code><i>connection_string</i></code> statement, transforms the schemas into Dataset resources, and writes the Datasets (as YAML) to <code><i>output_filename</i></code>. 

    The connection to your database isn't dynamic. If you update your database schemas, you have to re-generate (or modify) your Dataset objects.

  </div>
  
  <div class="label">ARGUMENTS</div>
  <div class="content">
    <div class="monoi">
      connection_string
    </div>
    <div class="content">
      An SQLAlchemy-compatible statement that connects to your database and reads one more schemas.
    </div>
  </div>
  <div class="content">
    <div class="monoi">
      output_filename
    </div>
    <div class="content">
      <div class="content">
        The name of the Dataset manifest file that the command will write. The value can be an absolute or relative path, and should include the <code>.yml</code> or <code>.yaml</code> extension.

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


