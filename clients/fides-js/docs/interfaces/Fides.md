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
existence of Fides *or* subscribe to the global `FidesInitialized` event (see
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

> **consent**: `Record`\<`string`, `boolean`\>

User's current consent preferences, formatted as a key/value object with:
- key: the applicable Fides `notice_key` (e.g. `data_sales_and_sharing`, `analytics`)
- value: `true` or `false`, depending on whether or not the current user
has consented to the notice

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

***

### fides\_string?

> `optional` **fides\_string**: `string`

User's current consent string(s) combined into a single value. The string
consists of three parts separated by commas in the format:
`TC_STRING,AC_STRING,GPP_STRING` where:

- TC_STRING: IAB TCF (Transparency & Consent Framework) string
- AC_STRING: Google's Additional Consent string, derived from TC_STRING
- GPP_STRING: IAB GPP (Global Privacy Platform) string

Note: The AC_STRING can only exist if TC_STRING exists, as it's derived from it.
When GPP is enabled, the GPP_STRING portion is automatically initialized during
FidesJS initialization, either preserving any existing GPP string or using a
default value. The GPP_STRING is independent and can exist with or without the
other strings.

#### Example

```ts
// Complete string with all parts:
console.log(Fides.fides_string);
// "CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA,1~61.70,DBABLA~BVAUAAAAAWA.QA"

// TC and AC strings only (no GPP):
console.log(Fides.fides_string);
// "CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA,1~61.70"

// GPP string only:
console.log(Fides.fides_string);
// ",,DBABLA~BVAUAAAAAWA.QA"
```

***

### initialized

> **initialized**: `boolean`

Whether or not FidesJS has finished initialization and has loaded the
current user's experience, consent preferences, etc.

NOTE: To be notified when initialization has completed, you can subscribe
to the `FidesInitialized` event. See [FidesEvent](FidesEvent.md) for details.

***

### getModalLinkLabel()

> **getModalLinkLabel**: (`options`?) => `string`

The modal's "Trigger link label" text can be customized, per regulation, for each language defined in the `experience`.

Use this function to get the label in the appropriate language for the user's current locale.
To always return in the default language only, pass the `disableLocalization` option as `true`.

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
    addEventListener("FidesInitialized", ( function() {
      document.getElementById('fides-modal-link-label').innerText = Fides.getModalLinkLabel();
    }));
  }
</script>
```

#### Parameters

| Parameter | Type |
| ------ | ------ |
| `options`? | `object` |
| `options.disableLocalization`? | `boolean` |

#### Returns

`string`

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

#### Returns

`void`

***

### gtm()

> **gtm**: () => `void`

Enable the Google Tag Manager (GTM) integration. This should be called
immediately after FidesJS is included, and once enabled, FidesJS will
automatically push all [FidesEvent](FidesEvent.md) events to the GTM data layer as
they occur, which can then be used to trigger/block tags in GTM based on
`Fides.consent` preferences or other business logic.

See the Google Tag Manager tutorial for more: [https://fid.es/configuring-gtm-consent](https://fid.es/configuring-gtm-consent)

#### Example

Enabling the GTM integration in your site's `<head>`:
```html
<head>
  <script src="path/to/fides.js"></script>
  <script>Fides.gtm()</script>
</head>
```

#### Returns

`void`

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
(see [Privacy Center FidesJS Hosting](/docs/dev-docs/js/privacy-center-fidesjs-hosting) for details).
You will then need to call `Fides.init()` manually at the appropriate time.

This function can also be used to reinitialize FidesJS. This is useful when
you're working on a single page application (SPA) and you want to modify any
FidesJS options after initialization - for example, switching between
regular/embedded mode with `fides_embed`, overriding the user's language with
`fides_locale`, etc. Doing so without passing a config will reinitialize
FidesJS with the initial configuration, but taking into account any new overrides
such as the `fides_overrides` global or the query params.

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

#### Parameters

| Parameter | Type |
| ------ | ------ |
| `config`? | `any` |

#### Returns

`Promise`\<`void`\>

***

### onFidesEvent()

> **onFidesEvent**: (`type`, `callback`) => () => `void`

An alternative way to subscribe to Fides events. The same events are supported, except the callback
receives the event details directly. This is useful in restricted environments where you can't
directly access `window.addEventListener`.

Returns an unsubscribe function that can be called to remove the event listener.

#### Example

```ts
const unsubscribe = Fides.onFidesEvent("FidesUpdated", (detail) => {
  console.log(detail.consent);
  unsubscribe();
});
```

#### Parameters

| Parameter | Type | Description |
| ------ | ------ | ------ |
| `type` | `any` | The type of event to listen for, such as `FidesInitialized`, `FidesUpdated`, etc. |
| `callback` | (`detail`) => `void` | The callback function to call when the event is triggered |

#### Returns

`Function`

##### Returns

`void`

***

### ~~reinitialize()~~

> **reinitialize**: () => `Promise`\<`void`\>

#### Deprecated

`Fides.init()` can now be used directly instead of `Fides.reinitialize()`.

#### Returns

`Promise`\<`void`\>

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
