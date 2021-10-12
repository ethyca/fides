# Evaluate your policy
_In this section, we'll review how to evaluate your policy and address any errors._

Now that we're done with all the setup, it's time to put your policy to the test! 


# Run an Evaluation

Running an evaluation locally is as easy as running a single line command from the CLI. 

Since we're running Fides locally, you can use the following command to evaluate your system:

```bash
fidesctl evaluate <path to resources>
```

Or, alternatively, if you'd like to see the Evaulation result from just a single resource type, you might try:

```bash
fidesctl evaluate system <path to resource>
```

If that command returns a *PASS* evaluation, then you're now in a known-good state and ready to set up automated CI workflows to make sure your application stays compliant with each PR. However, if that command returns a *FAILED* evaluation, you should have received feedback as to why it failed. 

```bash
root@fa175a43c077:/fides/fidesctl# fidesctl evaluate demo_resources
Loading resource manifests from: demo_resources
Taxonomy successfully created.
----------
Processing registry resources...
CREATED 1 registry resources.
UPDATED 0 registry resources.
SKIPPED 0 registry resources.
----------
Processing dataset resources...
CREATED 1 dataset resources.
UPDATED 0 dataset resources.
SKIPPED 0 dataset resources.
----------
Processing policy resources...
CREATED 1 policy resources.
UPDATED 0 policy resources.
SKIPPED 0 policy resources.
----------
Processing system resources...
CREATED 2 system resources.
UPDATED 0 system resources.
SKIPPED 0 system resources.
----------
Loading resource manifests from: demo_resources
Taxonomy successfully created.
Evaluating the following policies:
demo_privacy_policy
----------
Checking for missing resources...
Executing evaluations...
Sending the evaluation results to the server...
Evaluation passed!
```

Congratulations, you've now created your annotated datasets, system-level business cases, and your policy for enforcement — You've laid the groundwork for a comprehensive data privacy software program at your organization! This is a great starting point for training your peers and colleagues on so they can evaluate their new code locally prior to committing any code to the repo. 

The final step will be to [integrate this with your CI](taxonomy.md) so that you can fully realize Fides' potential.  Allowing Fides evaluate calls to be triggered from your pipeline will be critical for automatically assessing compliance at build time going forward. 
