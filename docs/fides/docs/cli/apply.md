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

td {
  padding-bottom: 14px;
}
</style>
# apply

<span class="label">NAME</span>

<div class="content">
<span class="mono">apply</span> &mdash; create or update your resources
</div>

<span class="label">SYNOPSIS</span>

<div class="content">
<pre><code>fidesctl apply <i>manifest_dir</i> [--dry] [--diff]</code></pre>
</div>

<span class="label">DESCRIPTION</span>

<div class="content">
The <code>apply</code> command reads the resource manifest files in <i>manifest_dir</i> and applies the resources to your server. If a named resource already exists, the resource is completely overwritten with the new description; if it doesn't exist, it's created.
<p>
As the command updates the server, it announces how many resources it has created, updated, and deleted.
</div>

<span class="label">OPTIONS</span>
<div class="content">
<table class="options">
  <col style="width:20%">
  <col style="width:80%">
  <tr>
    <td>"Dry run" mode. As it applies the resource manifest files, <code>apply</code> prints out the number of resources it would create, update, and delete, but it doesn't actually apply the changes to your server.</td>

  </tr>
  <tr>
    <td class="mono">--diff</td>
    <td>In addition to printing the number of changed resources, the command prints a diff between the server's old and new states. The diff is in <a href="https://pypi.org/project/deepdiff/" target="_blank">Python DeepDiff</a> format.</td>
  </tr>
</table>
</div>


 

