<div class="cli">
  <h1>reset-db</h1>

  <div class="label">NAME</div>

  <div class="content">
    <span class="mono">reset-db</span> &mdash; initialize and launch your Fides policy database
  </div>

  <div class="label">SYNOPSIS</div>

  <div class="content">
    <pre><code>fidesctl reset-db [-y/--yes]</code></pre>
  </div>

  <div class="label">DESCRIPTION</div>

  <div class="content">
    The <code>reset-db</code> command removes the resources that you added through previous <a href="/cli/apply/"><code>apply</code></a> calls. The database is then re-initialized through <code>init&#8209;db</code>.
  </div>

  
  <div class="label">OPTIONS</div>
    <div class="content">
    <div class="mono">
      -y/--yes
    </div>
    <div class="content">
      Before it removes the resources, <code>reset-db</code> prompts you to confirm the removal. The <code>&#8209;y</code>/<code>&#8209;&#8209;yes</code> option suppresses the prompt; resources are removed without your confirmation.
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
