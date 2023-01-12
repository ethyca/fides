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

If the user visits the Privacy Center and removes their consent for advertising, this choice is
saved in their browser. Subsequent visits to pages that include `fides-consent.js` will have 
`Fides.consent.data_sales` set to `false`.


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

### Shopify

To integrate with Shopify's [Consent Tracking API](https://shopify.dev/api/consent-tracking?shpxid=7e81a186-C696-4E23-F327-E7F38E5FF5EE#consent-collection),
call `Fides.shopify(options)`, where options is an with the following properties:

- `tracking`: The only consent option Shopify currently supports. Refer to their [visitor tracking](https://shopify.dev/api/consent-tracking#visitor-tracking) documentation.

For example, with the default Privacy Center configuration:

```html
<head>
  <!-- The script can be loaded in the store's theme, or in a custom pixel. -->
  <script src="example.com/privacy-center/fides-consent.js"></script>
  <script>Fides.shopify({ tracking: Fides.consent.data_sales })</script>
<head>
```

Note that `data_sales` is just an example cookie key. You may configure other data uses that should
be considered tracking, whose cookie key you would pass as the `tracking` option instead.

##  fides-consent.mjs & fides-consent.d.ts

This package also exports its library (`src/lib`) as a module the Privacy Center can import. This ensures the Privacy Center uses the exact same logic for reading & writing cookie data. This module is only used locally for convenience and is not published.

Note that this module does _not_ define the `Fides.consent` global, as that is unnecessary when using modules.


## Building

This package is built and hosted independently from the privacy center, but the privacy center's scripts should automatically keep it up-to-date automatically.

To build the minified script it manually:

```sh
# From fides-consent
npm run build
# From privacy-center
npm run build:fides-consent
```

Or, to watch for changes and build without minification:

```sh
# From fides-consent
npm run watch
```
