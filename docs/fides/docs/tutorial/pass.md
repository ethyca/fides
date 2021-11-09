# Manage Google Analytics with Fidesctl

By default, Google Analytics disables "IP Anonymization" (see [the documentation](https://developers.google.com/analytics/devguides/collection/gtagjs/ip-anonymization) for more information). The "Minimize User Identifiable Data" fidesctl Policy resource created earlier in this tutorial is configured to reject data collection of this nature.

---

**POP QUIZ!**

There are two options to remedy this situation, and to get the `make fidesctl-evaluate` command to pass. Which option is best?

1. Modify the "Minimize User Identifiable Data" policy resource to accept data collection of this nature
1. Modify the Google Analyitcs implementation such that it becomes compliant with the "Minimize User Identifiable Data" policy

<details>
  <summary>Click to see the correct answer</summary><br/>

  **Option 2** is the best path forward: the Google Analytics implementation should be modified, not the "Minimize User Identifiable Data" policy resource. The policy resource's configuration is dictated by the app's Privacy Policy, and changes could lead to larger compliance issues throughout the system.
</details>

---

## Enable IP Anonymization

Open the `flaskr/templates/base.html` file in your favorite editor, and add the following line just above the closing `<script>` tag in the Google Analytics script:

```diff
{% if config['GOOGLE_ANALYTICS_ID'] %}
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={{ config['GOOGLE_ANALYTICS_ID'] }}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag("js", new Date());
        gtag("config", "{{ config['GOOGLE_ANALYTICS_ID'] }}");
+       gtag("config", "{{ config['GOOGLE_ANALYTICS_ID'] }}", { 'anonymize_ip': true });
    </script>
{% endif %}
```

## Update the Google Analytics System Resource

Now that the data collection practices in the Google Analytics script have changed, the associated fidesctl System resource should be updated accordingly. Open the `fides_resources/google_analytics_system.yml` file in your favorite editor, and modify the last line (the `data_qualifier` configuration) so that it reads:

```yml
data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized
```

By removing the final `identified` key of the Fides taxonomy, the updated nature of the data collection practices used in this System resource now aligns with the actual behavior of the updated Google Analytics script.

## Evaluate the Fidesctl Policies

Execute the `make fidesctl-evaluate` command one final time. You should see the following output:

```
Evaluating policy with fidesctl...
./venv/bin/fidesctl evaluate --dry fides_resources
Loading resource manifests from: fides_resources
Taxonomy successfully created.
----------
Processing dataset resources...
WOULD CREATE 0 dataset resources.
WOULD UPDATE 0 dataset resources.
WOULD SKIP 1 dataset resources.
----------
Processing system resources...
WOULD CREATE 0 system resources.
WOULD UPDATE 1 system resources.
WOULD SKIP 1 system resources.
----------
Processing policy resources...
WOULD CREATE 0 policy resources.
WOULD UPDATE 0 policy resources.
WOULD SKIP 1 policy resources.
----------
Loading resource manifests from: fides_resources
Taxonomy successfully created.
Evaluating the following policies:
flaskr_policy
----------
Checking for missing resources...
Executing evaluations...
Evaluation passed!
```

The fidesctl policy evaluation passes!

## Check Your Progress

After making the above changes, your app should resemble the state of the [`ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) at the [`fidesctl-demo`](https://github.com/ethyca/fidesdemo/releases/tag/fidesctl-demo) tag.
