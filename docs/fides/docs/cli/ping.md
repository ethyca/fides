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
# ping

<span class="label">NAME</span>

<div class="content">
<span class="mono">ping</span> &mdash; query the health of the fides API host
</div>

<span class="label">SYNOPSIS</span>

<div class="content">
<pre><code>fidesctl ping </code></pre>
</div>

<span class="label">DESCRIPTION</span>

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

 

