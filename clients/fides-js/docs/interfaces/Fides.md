# Interface: Fides

Once FidesJS is initialized, it exports this global object to `window.Fides`
as the main API to integrate into your web applications.

You can then use `Fides` in your JavaScript code to check the user's current
consent preferences (e.g. `if (Fides.consent.marketing) { ... }`), enable
FidesJS integrations (e.g. `Fides.gtm()`), programmaticaly show the FidesJS
UI (e.g. `Fides.showModal()`) and more. See the full list of properties below
for details.

NOTE: FidesJS will need to be downloaded, executed, and initialized before
the `Fides` object is available. Therefore, your code should check for the
existence of Fides *or* subscribe to the global `FidesReady` event (see
[FidesEvent](FidesEvent.md)) for details) before using the `Fides` object in your own code.

## Example

```html
<head>
  <script src="path/to/fides.js"></script>
</head>
<body>
  <!--- ...later, in your own application code... --->
  <script>
    // Query the current user's consent preferences
    if (Fides && Fides.consent.data_sales_and_sharing) {
      // Enable advertising scripts
      console.log("Current user has opt-in consent for the `data_sales_and_sharing` privacy notice!");
    }
  </script>
</body>
```

## Properties

### consent

> **consent**: `Record`\<`string`, `string` \| `boolean`\>

User's current consent preferences, formatted as a key/value object with:
- key: the applicable Fides `notice_key` (e.g. `data_sales_and_sharing`, `analytics`)
- value:
  - `true` or `false` boolean values (where true means opt-in/consent granted, false means opt-out/consent declined)
  - or one of these string values:
    - `"opt_in"` - user has explicitly opted in to this notice
    - `"opt_out"` - user has explicitly opted out of this notice
    - `"acknowledge"` - user has acknowledged this notice (for notice-only consent mechanisms)
    - `"not_applicable"` - notice is not applicable to the user's region/context

Note that FidesJS will automatically set default consent preferences based
on the type of notice - so, for example a typical "opt-in" analytics notice
will be given a default value of `false`. This allows writing very simple
(and readable!) code to check a user's consent preferences.

The specific keys provided in the `Fides.consent` property are determined
based on your Fides configuration, and are provided to the browser based on
the user's location, property ID, etc.

#### Examples

A `Fides.consent` value showing the user has opted-out of data sales & sharing:
```ts
{
  "data_sales_and_sharing": false
}
```

A `Fides.consent` value showing the user has opted-in to analytics, but not marketing:
```ts
{
  "analytics": true,
  "marketing": false
}
```

A `Fides.consent` value showing the user has opted-in to analytics, but not marketing using consent mechanism strings:
```ts
{
  "analytics": "opt_in",
  "marketing": "opt_out"
}
```

A `Fides.consent` value showing a notice-only consent mechanism with acknowledgment:
```ts
{
  "terms_of_service": "acknowledge"
}
```

***

### fides\_string?

> `optional` **fides\_string**: `string`

User's current consent string(s) combined into a single value. This is used by
FidesJS to store IAB consent strings from various frameworks such as TCF, GPP,
and Google's "Additional Consent" string. Additionally, we support passing a
Notice Consent string, which is a base64 encoded string of the user's Notice
Consent preferences. See [FidesOptions.fides_string](FidesOptions.md#fides_string) for more details.

The string consists of four parts separated by commas in the format:
`TC_STRING,AC_STRING,GPP_STRING,NC_STRING` where:

- TC_STRING: IAB TCF (Transparency & Consent Framework) string
- AC_STRING: Google's Additional Consent string
- GPP_STRING: IAB GPP (Global Privacy Platform) string
- NC_STRING: Base64 encoded string of the user's Notice Consent preferences.

#### Example

```ts
console.log(Fides.fides_string);
// "CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA,2~61.70~dv.33,DBABLA~BVAUAAAAAWA.QA,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjowLCJhbmFseXRpY3MiOjF9"
```

***

### initialized

> **initialized**: `boolean`

Whether or not FidesJS has finished initialization and has loaded the
current user's experience, consent preferences, etc.

NOTE: To be notified when initialization has completed, you can subscribe
to the `FidesReady` event. See [FidesEvent](FidesEvent.md) for details.

***

### getModalLinkLabel()

> **getModalLinkLabel**: (`options`?) => `string`

The modal's "Trigger link label" text can be customized, per regulation, for each language defined in the `experience`.

Use this function to get the label in the appropriate language for the user's current locale.
To always return in the default language only, pass the `disableLocalization` option as `true`.

#### Parameters

| Parameter | Type |
| ------ | ------ |
| `options`? | `object` |
| `options.disableLocalization`? | `boolean` |

#### Returns

`string`

#### Examples

Get the link text in the user's current locale (eg. Spanish):
```ts
console.log(Fides.getModalLinkLabel()); // "Tus preferencias de privacidad"
```

Get the link text in the default locale to match other links on the page:
```ts
console.log(Fides.getModalLinkLabel({ disableLocalization: true })); // "Your Privacy Choices"
```

Apply the link text to a custom modal link element on Fides initialization:
```html
<button class="my-custom-show-modal" id="fides-modal-link-label" onclick="Fides.showModal()"><button>
<script id="fides-js">
  function() {
    addEventListener("FidesReady", ( function() {
      document.getElementById('fides-modal-link-label').innerText = Fides.getModalLinkLabel();
    }));
  }
</script>
```

***

### showModal()

> **showModal**: () => `void`

Display the FidesJS modal component on the page, if the current user's
session (location, property ID, etc.) matches an `experience` with a modal
component. If the `experience` does not match, this function has no effect
and can be called safely at any time.

This function is designed to be used to programmatically show the FidesJS
modal via an `onclick` handler on a "modal link" element on the page.
However, since the modal is optional, this link should only be shown when
applicable. To make it easy to dynamically show/hide this "modal link",
FidesJS will automatically add the CSS class `fides-overlay-modal-link-shown`
to the `<body>` when applicable. This class can then be used to show/hide a
link on the page via CSS rules - see the example below!

When not used as a click handler, `Fides.showModal()` can be called
programmatically at any time from your own custom JavaScript logic as
desired.

NOTE: If using custom JavaScript to show the modal, you may also want to set
the `modalLinkId` global setting on the Fides Privacy Center to prevent the
automated searching for, and binding the click event to, the modal link. If using
Fides Cloud, contact Ethyca Support for details on adjusting global settings.

This function is not available for Headless experiences.

#### Returns

`void`

#### Examples

Showing the FidesJS modal via an `onclick` handler on a custom button element:
```html
<button class="my-custom-show-modal" onclick="Fides.showModal()">
  Your Privacy Choices
</button>
```

Another option, using a custom link element instead:
```html
<a role="button" class="my-custom-show-modal" onclick="Fides.showModal()">
  Your Privacy Choices
</a>
```

Showing/hiding the custom element using the `fides-overlay-modal-link` CSS class:
```css
/* Hide the custom element by default */
.my-custom-show-modal {
  display: none;
}
/* Only show the custom element when applicable */
.fides-overlay-modal-link-shown .my-custom-show-modal {
  display: inline;
}
```

Showing the FidesJS modal programmatically in a JavaScript function:
```ts
function myCustomShowModalFunction() {
  console.log("Displaying FidesJS consent modal")
  if (window.Fides) {
    window.Fides.showModal();
  }
}
```

***

### gtm()

> **gtm**: (`options`?) => `void`

Enable the Google Tag Manager (GTM) integration. This should be called
immediately after FidesJS is included, and once enabled, FidesJS will
automatically push all [FidesEvent](FidesEvent.md) events to the GTM data layer as
they occur, which can then be used to trigger/block tags in GTM based on
`Fides.consent` preferences or other business logic.

See the [Google Tag Manager tutorial](/tutorials/consent-management/consent-management-configuration/google-tag-manager-consent-mode) for more.

#### Parameters

| Parameter | Type | Description |
| ------ | ------ | ------ |
| `options`? | `object` | Optional configuration for the GTM integration |
| `options.non_applicable_flag_mode`? | `"omit"` \| `"include"` | Controls how non-applicable privacy notices are handled in the data layer. Can be "omit" (default) to exclude non-applicable notices, or "include" to include them with a default value. |
| `options.flag_type`? | `"boolean"` \| `"consent_mechanism"` | Controls how consent values are represented in the data layer. Can be "boolean" (default) for true/false values, or "consent_mechanism" for string values like "opt_in", "opt_out", "acknowledge", "not_applicable". |

#### Returns

`void`

#### Examples

Basic usage in your site's `<head>`:
```html
<head>
  <script src="path/to/fides.js"></script>
  <script>Fides.gtm()</script>
</head>
```

With options to include non-applicable notices and use consent mechanism strings:
```html
<head>
  <script src="path/to/fides.js"></script>
  <script>
    Fides.gtm({
      non_applicable_flag_mode: "include",
      flag_type: "consent_mechanism"
    });
  </script>
</head>
```

***

### shopify()

> **shopify**: (`options`?) => `void`

Enable the Shopify integration. This should be called immediately after
FidesJS is included. Once enabled, FidesJS will automatically push all
consent updates to Shopify's Customer Privacy API, which can then be used
to ensure consent is enforced on Shopify-managed apps & pixels.

See the [Shopify installation tutorial](/tutorials/consent-management/consent-management-configuration/install-fides-shopify) for more.

#### Parameters

| Parameter | Type | Description |
| ------ | ------ | ------ |
| `options`? | `object` | Optional configuration for the Shopify integration |
| `options.sale_of_data_default`? | `boolean` | Controls the default value for Shopify's "sale of data" consent. If `true`, the user will be opted-in by default. If `false` or omitted, the user will be opted-out by default. |

#### Returns

`void`

#### Examples

Basic usage in your site's `<head>`:
```html
<head>
  <script src="path/to/fides.js"></script>
  <script>
    if (typeof Fides !== 'undefined' && typeof Fides.shopify === 'function') {
      Fides.shopify();
    }
  </script>
</head>
```

With options to default "sale of data" to opt-in:
```html
<head>
  <script src="path/to/fides.js"></script>
  <script>
    if (typeof Fides !== 'undefined' && typeof Fides.shopify === 'function') {
      Fides.shopify({ sale_of_data_default: true });
    }
  </script>
</head>
```

***

### init()

> **init**: (`config`?) => `Promise`\<`void`\>

Initializes FidesJS with an initial configuration object.

In most cases, you should never have to call this directly, since
Fides Cloud will automatically bundle a `Fides.init(...)` call server-side
with the appropriate configuration options for the user's session based on
their location, property ID, and the matching experience config from Fides.

However, initialization can be called manually if needed - for example to delay
initialization until after your own custom JavaScript has run to set up some
config options. In this case, you can disable the automatic initialization
by including the query param `initialize=false` in the Fides script URL
(see [Privacy Center FidesJS Hosting](/dev-docs/js/privacy-center-fidesjs-hosting) for details).
You will then need to call `Fides.init()` manually at the appropriate time.

This function can also be used to reinitialize FidesJS. This is useful when
you're working on a single page application (SPA) and you want to modify any
FidesJS options after initialization - for example, switching between
regular/embedded mode with `fides_embed`, overriding the user's language with
`fides_locale`, etc. Doing so without passing a config will reinitialize
FidesJS with the initial configuration, but taking into account any new overrides
such as the `fides_overrides` global or the query params.

#### Parameters

| Parameter | Type |
| ------ | ------ |
| `config`? | `any` |

#### Returns

`Promise`\<`void`\>

#### Example

Disable FidesJS initialization and trigger manually instead:
```html
<head>
  <script src="https://privacy.example.com/fides.js?initialize=false"></script>
</head>
<body>
  <!--- Later, in your own application code... -->
  <script>Fides.init()</script>
</body>
```
Configure overrides after loading Fides.js tag.
```html
<head>
  <script src="path/to/fides.js">
    // Loading Fides.js before setting window.fides_overrides requires re-initialization
  </script>

  <script>
    function onChange(newData) {
      // Update Fides options
      window.fides_overrides = window.fides_overrides || {};
      window.fides_overrides = {
        fides_locale: newData,
      };

      // Reinitialize FidesJS
      window.Fides.init();
    };
  </script>
</head>
```

***

### onFidesEvent()

> **onFidesEvent**: (`type`, `callback`) => () => `void`

An alternative way to subscribe to Fides events. The same events are supported, except the callback
receives the event details directly. This is useful in restricted environments where you can't
directly access `window.addEventListener`.

Returns an unsubscribe function that can be called to remove the event listener.

#### Parameters

| Parameter | Type | Description |
| ------ | ------ | ------ |
| `type` | `any` | The type of event to listen for, such as `FidesReady`, `FidesUpdated`, etc. |
| `callback` | (`detail`) => `void` | The callback function to call when the event is triggered |

#### Returns

`Function`

##### Returns

`void`

#### Example

```ts
const unsubscribe = Fides.onFidesEvent("FidesUpdated", (detail) => {
  console.log(detail.consent);
  unsubscribe();
});
```

***

### ~~reinitialize()~~

> **reinitialize**: () => `Promise`\<`void`\>

#### Returns

`Promise`\<`void`\>

#### Deprecated

`Fides.init()` can now be used directly instead of `Fides.reinitialize()`.

***

### shouldShowExperience()

> **shouldShowExperience**: () => `boolean`

Check if the FidesJS experience should be shown to the user. This function
will return `true` if the user's session (location, property ID, etc.)
matches an `experience` with a banner component, and the user has not yet
interacted with the banner (e.g. by accepting or rejecting the consent
preferences) or in the case when the previous consent is no longer valid.

#### Returns

`boolean`

***

### encodeNoticeConsentString()

> **encodeNoticeConsentString**: (`consent`) => `string`

Encode the user's consent preferences into a Notice Consent string. See [FidesOptions.fides_string](FidesOptions.md#fides_string) for more details.

#### Parameters

| Parameter | Type | Description |
| ------ | ------ | ------ |
| `consent` | `Record`\<`string`, `boolean` \| `0` \| `1`\> | The user's consent preferences to encode. (Numeric values are supported for smaller string results and will be decoded to boolean values) |

#### Returns

`string`

#### Example

```ts
const encoded = Fides.encodeNoticeConsentString({data_sales_and_sharing:0,analytics:1});
console.log(encoded); // "eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjowLCJhbmFseXRpY3MiOjF9"
```

***

### decodeNoticeConsentString()

> **decodeNoticeConsentString**: (`base64String`) => `object`

Decode a Notice Consent string into a user's consent preferences. See [FidesOptions.fides_string](FidesOptions.md#fides_string) for more details.

#### Parameters

| Parameter | Type | Description |
| ------ | ------ | ------ |
| `base64String` | `string` | The Notice Consent string to decode. |

#### Returns

`object`

#### Example

```ts
const decoded = Fides.decodeNoticeConsentString("eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjowLCJhbmFseXRpY3MiOjF9");
console.log(decoded); // {data_sales_and_sharing: false, analytics: true}
```

***

### geolocation?

> `optional` **geolocation**: `any`

The detected geolocation that Fides uses to determine the user's experience.
This field is read-only.

#### Example

```ts
{
  "country": "ca",
  "location": "ca-on",
  "region": "on"
}
```

***

### locale

> **locale**: `string`

The detected i18n locale that Fides uses to determine the language shown to the user.

#### Example

```ts
"en"
```

This field is read-only.

***

### identity

> **identity**: `Record`\<`string`, `string`\>

The user's identity values, which only include a copy of the fides user device id that we store in the fides_consent cookie e.g.

#### Example

```ts
{
  "fides_user_device_id": "1234-"
}
```

This field is read-only.

***

### updateConsent()

> **updateConsent**: (`options`) => `Promise`\<`void`\>

Updates user consent preferences with either a `consent` object or `fidesString`.
If both are provided, `fidesString` takes priority.

#### Parameters

| Parameter | Type | Description |
| ------ | ------ | ------ |
| `options` | `object` | Options for updating consent |
| `options.consent`? | `Record`\<`string`, `string` \| `boolean`\> | Object mapping notice keys to consent values: - Boolean values: `true` (opt-in/consent granted) or `false` (opt-out/consent declined) - String values: - `"opt_in"` - user has explicitly opted in to this notice - `"opt_out"` - user has explicitly opted out of this notice - `"acknowledge"` - ONLY valid for notices with "notice_only" consent mechanism |
| `options.fidesString`? | `string` | A Fides string containing encoded consent preferences |
| `options.validation`? | `"throw"` \| `"warn"` \| `"ignore"` | Controls validation behavior: "throw" (default), "warn", or "ignore" - "throw": Throws an error if any consent value is invalid (default) - "warn": Logs a warning if any consent value is invalid, but continues processing - "ignore": Silently accepts invalid values without validation |

#### Returns

`Promise`\<`void`\>

#### Examples

Update consent using notice keys and boolean values:
```ts
Fides.updateConsent({
  consent: {
    data_sales_and_sharing: false,
    analytics: true
  }
});
```

Update consent using string values instead of booleans:
```ts
Fides.updateConsent({
  consent: {
    data_sales_and_sharing: "opt_out",
    analytics: "opt_in",
    terms_of_service: "acknowledge"
  }
});
```

Update consent using a fidesString:
```ts
Fides.updateConsent({
  fidesString: ",,,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjowLCJhbmFseXRpY3MiOjF9"
});
```

Control validation behavior:
```ts
// With validation="warn" - logs warnings but doesn't throw errors
Fides.updateConsent({
  consent: { notice_key: invalidValue },
  validation: "warn"
});

// With validation="ignore" - silently accepts invalid values
Fides.updateConsent({
  consent: { notice_key: invalidValue },
  validation: "ignore"
});
```
