<style type='text/css'>
.label {
  color: slategray;
  font-size: 18px;
  font-style: bold;
}
.content {
  margin-left:  24px;
  margin-bottom:  40px;
}

.options {
  border:  none;

}

.mono {
  font-family: monospace;
  font-weight: bold;
}

.tag {
  padding: 0 4px 0 4px;
  background: #fedd29;
  color: #002da9;
  border: solid 1px #ce122a;
  box-shadow: inset 0 0 0 1px #ce122a; 
}

.comment {
  color:  crimson;
  font-style:  italic;
}
.comment::before {
  content:  "<<< ";
}

.comment::after {
  content:  " >>>";
}
td {
  padding-bottom: 14px;
}
</style>
# evaluate

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
  <p>If you want to evaluate a single policy, use the <code>--fides-key</code> option, passing the fides key of the policy you wish to evaluate.
  </p>
  <p>
    Keep in mind that <code>evaluate</code> calls <code>apply</code> for you; you don't have to call it yourself before you call this command.
  </p>
</div>
<span class="label">OPTIONS</span>
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
    <span class="tag">Future</span> An optional message that you can attach to the evaluation for logging and debugging purposes. This option is currently unimplemented. <span class="comment">The message is attached to the evaluate object, but I don't see any mechanism for retrieving it</span>
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





