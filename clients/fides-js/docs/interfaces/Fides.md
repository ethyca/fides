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

**`Example`**

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

## Table of contents

### Properties

- [consent](Fides.md#consent)
- [fides\_string](Fides.md#fides_string)
- [initialized](Fides.md#initialized)
- [showModal](Fides.md#showmodal)
- [getModalLinkLabel](Fides.md#getmodallinklabel)
- [gtm](Fides.md#gtm)
- [init](Fides.md#init)

## Properties

### consent

• **consent**: `Record`\<`string`, `boolean`\>

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

**`Example`**

A `Fides.consent` value showing the user has opted-out of data sales & sharing:
```ts
{
  "data_sales_and_sharing": false
}
```

**`Example`**

A `Fides.consent` value showing the user has opted-in to analytics, but not marketing:
```ts
{
  "analytics": true,
  "marketing": false
}
```

___

### fides\_string

• `Optional` **fides\_string**: `string`

User's current consent string(s) combined into a single value. Currently,
this is used by FidesJS to store IAB consent strings from various
frameworks such as TCF, GPP, and Google's "Additional Consent" string.

**`Example`**

Example `fides_string` showing a combination of:
- IAB TC string: `CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA`
- Google AC string: `1~61.70`
```ts
console.log(Fides.fides_string); // CPzHq4APzHq4AAMABBENAUEAALAAAEOAAAAAAEAEACACAAAA,1~61.70
```

___

### initialized

• **initialized**: `boolean`

Whether or not FidesJS has finished initialization and has loaded the
current user's experience, consent preferences, etc.

NOTE: To be notified when initialization has completed, you can subscribe
to the `FidesInitialized` event. See [FidesEvent](FidesEvent.md) for details.

___

### showModal

• **showModal**: () => `void`

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

**`Example`**

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

**`Example`**

Showing the FidesJS modal programmatically in a JavaScript function:
```ts
function myCustomShowModalFunction() {
  console.log("Displaying FidesJS consent modal")
  if (window.Fides) {
    window.Fides.showModal();
  }
}
```

#### Type declaration

▸ (): `void`

##### Returns

`void`

___

### getModalLinkLabel

• **getModalLinkLabel**: (`options?`: \{ `disableLocalization`: `boolean`  }) => `string`

The modal's "Trigger link label" text can be customized, per regulation, for each language defined in the `experience`.

Use this function to get the label in the appropriate language for the user's current locale.
To always return in the default language only, pass the `disableLocalization` option as `true`.

**`Example`**

Getting the link text in the user's current locale (eg. Spanish):
```ts
console.log(Fides.getModalLinkLabel()); // "Tus preferencias de privacidad"
```

Getting the link text in the default locale to match other links on the page:
```ts
console.log(Fides.getModalLinkLabel({ disableLocalization: true })); // "Your Privacy Choices"
```

**`Example`**

Applying the link text to a custom modal link element:
```html
<button class="my-custom-show-modal" id="fides-modal-link-label" onclick="Fides.showModal()" />
<script>
 document.getElementById('fides-modal-link-label').innerText = Fides.getModalLinkLabel();
</script>
```

#### Type declaration

▸ (`options?`): `string`

##### Parameters

| Name | Type |
| :------ | :------ |
| `options?` | `Object` |
| `options.disableLocalization` | `boolean` |

##### Returns

`string`

___

### gtm

• **gtm**: () => `void`

Enable the Google Tag Manager (GTM) integration. This should be called
immediately after FidesJS is included, and once enabled, FidesJS will
automatically push all [FidesEvent](FidesEvent.md) events to the GTM data layer as
they occur, which can then be used to trigger/block tags in GTM based on
`Fides.consent` preferences or other business logic.

See the Google Tag Manager tutorial for more: [https://fid.es/configuring-gtm-consent](https://fid.es/configuring-gtm-consent)

**`Example`**

Enabling the GTM integration in your site's `<head>`:
```html
<head>
  <script src="path/to/fides.js"></script>
  <script>Fides.gtm()</script>
</head>
```

#### Type declaration

▸ (): `void`

##### Returns

`void`

___

### init

• **init**: (`config`: `any`) => `Promise`\<`void`\>

Initializes FidesJS with an initial configuration object.

NOTE: In most cases, you should never have to call this directly, since
Fides Cloud will automatically bundle a `Fides.init(...)` call server-side
with the appropriate configuration options for the user's session based on
their location, property ID, and the matching experience config from Fides.

#### Type declaration

▸ (`config`): `Promise`\<`void`\>

##### Parameters

| Name | Type |
| :------ | :------ |
| `config` | `any` |

##### Returns

`Promise`\<`void`\>
