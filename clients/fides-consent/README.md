# fides-consent.js

This package builds a script that can be used in a page to access the consent choices a user has made using the Privacy Center.

To use the script, include it in your page:

```html
<head>
  <!-- Include before any scripts which need consent. -->
  <script src="example.com/privacy-center/fides-consent.js"></script>
<head>
```

*Note:* Replace `example.com/privacy-center` with the URL where you are hosting the Privacy Center.

Then, in code that need user consent, check the consent map under the `Fides` global variable:

```js
if (Fides.consent.data_sales) {
  // User has opted in.
} else {
  // User has opted out.
}
```

In this example, `data_sales` is a cookie key that has been [configured in the Privacy Center](/clients/privacy-center/config/config.json).

## Configuration

The build process for this package pulls in the consent configuration from the Privacy Center's
`config.json`. This includes the `cookieKeys` for each consent item as the default options for a
user that has not modified their consent. 

For example, the default configuration includes a consent option for advertising:

```json
{
  "consent": {
    "consentOptions": [
      {
        "fidesDataUseKey": "advertising",
        "name": "Data Sales or Sharing",
        "default": true,
        "cookieKeys": ["data_sales"]
      }
    ]
  }
}
```

When a user visits a page that includes `fides-consent.js` with this configuration, the value of
`Fides.consent.data_sales` will be set to `true` by default.

If the user visits the Privacy Center and removes their consent for `advertising`, this choice is
saved in their browser. Subsequent visits to pages that include `fides-consent.js` will have 
`Fides.consent.data_sales` set to `false`.

Multiple data uses can refer to the same cookie key. A user must consent to _all_ of those data uses
for the cookie key to be true. For example, with the default configuration:

```json
{
  "consent": {
    "consentOptions": [
      {
        "fidesDataUseKey": "advertising.first_party",
        "name": "Email Marketing",
        "default": true,
        "cookieKeys": ["tracking"]
      },
      {
        "fidesDataUseKey": "improve",
        "name": "Product Analytics",
        "default": true,
        "cookieKeys": ["tracking"]
      }
    ]
  }
}
```

By default, `Fides.consent.tracking` will be set to `true`. If the user removes their consent for 
`advertising.first_party`, `improve`, or both, then `Fides.consent.tracking` will be set to `false`.

### Consent Context

The `default` specified in a consent option is applied when a user has not made any consent choices
(for example, if they have not visited the Privacy Center). This default value can be:

- `true`: Behave as if the user has granted consent.
- `false`: Behave as if the user has revoked their consent.

However, this choice may need to be different based on information provided by the user's browser:
their _Consent Context_.

Currently, the only context that can be used is whether the user has enabled [Global Privacy Control](https://globalprivacycontrol.org/#about). To configure a default value which depends on this context, pass an object with
the following properties: 

- `value`: The consent boolean that applies when there is no relevant consent context.
- `globalPrivacyControl`. The consent boolean that applies the user has enabled GPC.

For example, with this configuration:

```json
{
  "consent": {
    "consentOptions": [
      {
        "fidesDataUseKey": "advertising.first_party",
        "name": "Email Marketing",
        "default": {
          "value": true,
          "globalPrivacyControl": false
        },
        "cookieKeys": ["data_sales"]
      },
      {
        "fidesDataUseKey": "provide.service",
        "name": "Core functionality",
        "default": true,
        "cookieKeys": ["functional"]
      }
    ]
  }
}
```

The `data_sales` cookie key will default to `true` (grant consent) **unless the user has enabled GPC** in which case consent will be revoked without the user having to go through the Privacy Center.

On the other hand, the `functional` cookie key will always default to `true` and the user must go through the Privacy Center to revoke consent.

## Integrations

### Google Tag Manager

Once Fides is loaded in a page, calling `Fides.gtm()` will push the user's consent
choices into GTM's dataLayer under `Fides.consent`.

```html
<head>
  <script src="example.com/privacy-center/fides-consent.js"></script>
  <script>Fides.gtm()</script>

  <!-- Include Google Tag Manager's script below. -->
<head>
```

A tag could then use this information to make consent choices:

```js
// Google Tag Manager Sandboxed JavaScript
const copyFromDataLayer = require('copyFromDataLayer');

var Fides = copyFromDataLayer('Fides') || { consent: {} }

if (Fides.consent.data_sales) {
  // The user has opted in.
}
```

### Meta Pixel


To integrate with [Meta's tracking pixel](https://developers.facebook.com/docs/meta-pixel/get-started),
call `Fides.meta(options)`, where options is an object with the following properties:

- `consent`: boolean - Whether the user consents to [Meta's use of cookies](https://developers.facebook.com/docs/meta-pixel/implementation/gdpr). 
  If `true`, consent it granted. Otherwise, consent is revoked.
- `dataUse`: boolean - Whether user's data can be [used by Meta](https://developers.facebook.com/docs/meta-pixel/implementation/ccpa).
  If `true`, Meta may use the data. Otherwise, Meta's Limited Data Use (LDU) mode will be be applied
  as if the user were in California.

For example, with the default Privacy Center configuration:

```html
<head>
  <script src="example.com/privacy-center/fides-consent.js"></script>
  <script>
    Fides.meta({ 
      consent: Fides.consent.tracking,
      dataUse: Fides.consent.data_sales
    })
  </script>
  
  <!-- Include Meta's pixel code below-->
<head>
```

This example omits [Meta's pixel code](https://developers.facebook.com/docs/meta-pixel/get-started).
`Fides.meta()` should be included before Meta's code, before your use of
`fbq('init', '{your-pixel-id-goes-here}')`.

### Shopify

To integrate with Shopify's [Consent Tracking API](https://shopify.dev/api/consent-tracking?shpxid=7e81a186-C696-4E23-F327-E7F38E5FF5EE#consent-collection),
call `Fides.shopify(options)`, where options is an object with the following properties:

- `tracking`: boolean - The only consent option Shopify currently supports. Refer to their [visitor tracking](https://shopify.dev/api/consent-tracking#visitor-tracking) documentation.

For example, with the default Privacy Center configuration:

```html
<head>
  <!-- The script can be loaded in the store's theme, or in a custom pixel. -->
  <script src="example.com/privacy-center/fides-consent.js"></script>
  <script>Fides.shopify({ tracking: Fides.consent.tracking })</script>
<head>
```

Note that `Fides.consent.tracking` is just an example cookie key. You may configure other data uses that should
be considered tracking, whose cookie key you would pass as the `tracking` option instead.

##  fides-consent.mjs & fides-consent.d.ts

This package also exports its library (`src/lib`) as a module the Privacy Center can import. This ensures the Privacy Center uses the exact same logic for reading & writing cookie data. This module is only used locally for convenience and is not published.

Note that this module does _not_ define the `Fides.consent` global, as that is unnecessary when using modules.


## Building

This package is built and hosted independently from the privacy center, but the privacy center's scripts should automatically keep it up-to-date automatically.

To build the minified script manually:

```sh
# From fides-consent
turbo run build
```

Or, to watch for changes and build without minification:

```sh
# From fides-consent
turbo run watch
```
