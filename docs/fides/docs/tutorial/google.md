# Add Google Analytics

To better understand the behavior of the app's users, add Google Analytics to the app and a Fidesctl System resource to annotate it.

## Define the App's Google Analytics Identifier

Open the `flaskr/__init__.py` file in your favorite editor, and define the `GOOGLE_ANALYTICS_ID` constant below line 7:

```python
GOOGLE_ANALYTICS_ID = "UA-xxxxxxxxx-y"
```

In the `create_app` function defined on line 11, include the Google Analytics ID value in the application's configuration by adding the following line below line 17:

```python
GOOGLE_ANALYTICS_ID=GOOGLE_ANALYTICS_ID,
```

## Add the Google Analytics Script

Open the `flaskr/templates/base.html` file in your favorite editor, and include the following at the beginning of the `<head>` tag:

```html
{% if config['GOOGLE_ANALYTICS_ID'] %}
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={{ config['GOOGLE_ANALYTICS_ID'] }}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag("js", new Date());
        gtag("config", "{{ config['GOOGLE_ANALYTICS_ID'] }}");
    </script>
{% endif %}
```

## Annotate a Fidesctl System Resource

To ensure that the app's policies can account for the data collected by Google Analytics, define a new Fidesctl System resource by adding a `google_analytics_system.yml` file to the `fides_resources` directory. This file should contain the following configuration:

```yml
system:
  - fides_key: google_analytics_system
    name: Google Analytics
    description: Hosted third party analytics to track and analyze user behaviour
    system_type: Third Party
    privacy_declarations:
      # See the Google Analytics documentation for a description of the possible
      # fields collected by the tracker, including page URL, referrer, cookie ID, etc.
      # https://developers.google.com/analytics/devguides/collection/analyticsjs/field-reference
      - name: Track & report on page views
        data_categories:
          - user.derived.identifiable.browsing_history
          - user.derived.identifiable.device.cookie_id
          - user.derived.identifiable.telemetry
          - user.derived.identifiable.location
          - user.derived.nonidentifiable
        data_use: improve
        data_subjects:
          - customer
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized
      # Google Analytics collects the user's IP address and derives geographic dimensions server-side.
      # See https://developers.google.com/analytics/devguides/reporting/realtime/dimsmets/geonetwork
      - name: Derive user geographic location
        data_categories:
          - user.derived.identifiable.device.ip_address
          - user.derived.identifiable.location
          - user.derived.identifiable
        data_use: improve
        data_subjects:
          - customer
        # With "IP Anonymization" enabled, IP addresses will be pseudonymized in Google Analytics
        # See https://developers.google.com/analytics/devguides/collection/gtagjs/ip-anonymization
        data_qualifier: aggregated.anonymized.unlinked_pseudonymized.pseudonymized
```

## Check Your Progress

After making the above changes, your app should resemble the state of the [`ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) at the [`fidesctl-add-google-analytics`](https://github.com/ethyca/fidesdemo/releases/tag/fidesctl-add-google-analytics) tag.

## Next: Manage Google Analytics with Fidesctl

Google Analytics is implemented and working correctly, but - oh no! - executing `make fidesctl-evaluate` shows a failure:

```
{
  "fides_key": "4e739b1b_732e_43b1_8747_e833905dfc4c_1635789050",
  "status": "FAIL",
  "details": [
    "Declaration (Derive user geographic location) of System (google_analytics_system) failed Rule (Minimize User Identifiable Data) from Policy (flaskr_policy)"
  ],
  "message": null
}
```

In the final step, enable the Fidesctl policy already in place to pass by [updating Google Analytics](pass.md).
