<div class="cli">
  <h1>ping</h1>

  <div class="label">NAME</div>

  <div class="content">
    <span class="mono">ping</span> &mdash; query the health of the fides API host
  </div>

  <div class="label">SYNOPSIS</div>

  <div class="content">
    <pre><code>fidesctl ping </code></pre>
  </div>

  <div class="label">DESCRIPTION</div>

  <div class="content">
    The <code>ping</code> command sends a message to the fides API healthcheck endpoint and prints the response. If the API host is up and running, you'll see this:

    ```
    $ fidesctl ping
    Pinging http://fidesctl:8080/health...
    {
      "data": {
        "message": "Fides service is healthy!"
      }
    }
    ```

    Any other response means the host isn't running or can't be reached. 

  </div>
</div>



