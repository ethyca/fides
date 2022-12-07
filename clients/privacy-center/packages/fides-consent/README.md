# fides-consent.js

This package builds a script that can be used in a page to access the consent choices a user has made using the Privacy Center.

TODO(#1516): Include URL of built & CDN hosted script.

To use the script, include it in your page:

```html
<head>
  <!-- Include before any scripts which need consent. -->
  <script src="fides-consent.js"></script>
<head>
```

Then, in code that need user consent, check the consent map under the `Fides` global variable:

```js
if (Fides.consent.data_sharing) {
  // User has opted in.
} else {
  // User has opted out.
}
```

In this example, `data_sharing` is a cookie key that has been [configured in the Privacy Center](/clients/privacy-center/config/config.json).

## fides-consent.mjs & fides-consent.d.ts

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
