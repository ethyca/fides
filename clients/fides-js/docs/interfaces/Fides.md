# Interface: Fides

Once FidesJS is initialized, it exports this global object to `window.Fides`
as the main API to integrate into your web applications.

TODO: more

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

## Properties

### consent

• **consent**: `Record`\<`string`, `boolean`\>

User's current consent preferences.

___

### fides\_meta

• **fides\_meta**: `object`

___

### fides\_string

• `Optional` **fides\_string**: `string`

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

### identity

• **identity**: `Record`\<`string`, `string`\>

User's current "identity" values, which are recorded

___

### init

• **init**: (`config`: `object`) => `Promise`\<`void`\>

Initialize FidesJS based

NOTE: In most cases, you should never have to call this directly, since
Fides Cloud will automatically bundle a `Fides.init(...)` call server-side
with the appropriate options for the user's session based on their
location, property ID, and the latest configuration options from Fides.

#### Type declaration

▸ (`config`): `Promise`\<`void`\>

##### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `config` | `object` | something |

##### Returns

`Promise`\<`void`\>

___

### initialized

• **initialized**: `boolean`

TODO

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
programmatically at any time from your own custom Javascript logic as
desired.

**`Example`**

Showing the FidesJS modal via an `onclick` handler on a custom link element:
```html
<a href="#" class="my-custom-link" onclick="Fides.showModal()">
  Your Privacy Choices
</a>
```

Showing/hiding the custom link element using the `fides-overlay-modal-link` CSS class:
```css
/* Hide the modal link by default */
.my-custom-link {
  display: none;
}
/* Only show the modal link when applicable */
.fides-overlay-modal-link-shown .my-custom-link {
  display: inline;
}
```

**`Example`**

Showing the FidesJS modal programmatically in a Javascript function:
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
