# ping &mdash; determine if the API server is up


### SYNOPSIS


**fidesctl ping**


### DESCRIPTION

The `ping` command sends a message to the fides API health endpoint and prints the response. If the API host is up and running, you'll see this:

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


### OPTIONS

**-h/--help**

Prints a synopsis of this command.






