# Interface: FidesLocaleEvent

FidesJS dispatches a `FidesLocaleUpdated` event when the user changes the
language using the language selector in the UI. This event is separate from
the consent-focused [FidesEvent](FidesEvent.md) types and has a simple structure
containing only the newly selected locale.

This event extends the standard
[CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)
interface and includes a [detail](FidesLocaleEvent.md#detail) object with the locale and timestamp.

## Example

```ts
window.addEventListener("FidesLocaleUpdated", (evt) => {
  console.log(`Language changed to: ${evt.detail.locale}`);
});
```

For more information on working with these kind of `CustomEvent` objects in
the browser, see the MDN docs:
[https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)

### Event Type

- `FidesLocaleUpdated`: Dispatched when the user changes the language using
the language selector in the FidesJS UI. This event fires after the locale
has been successfully changed and applied to the UI.

**Note**: This event is intentionally separate from consent-related
[FidesEvent](FidesEvent.md) types. It does not include consent data or the complex
`extraDetails` structure. It will not be forwarded to GTM or other
consent-focused integrations.

## Extends

- `CustomEvent`

## Properties

### detail

> **detail**: `object`

Event properties passed when the locale is updated.

#### locale

> **locale**: `string`

The newly selected locale (e.g., "en", "fr", "es", "de") which will match the Fides.locale value. See [Fides.locale](Fides.md#locale) for detail.

#### timestamp?

> `optional` **timestamp**: `number`

High-precision timestamp from [performance.mark()](https://developer.mozilla.org/en-US/docs/Web/API/Performance/mark)
representing when this event was created. The timestamp is measured in milliseconds since page load.

May be undefined if the Performance API is not available.

#### Example

```ts
window.addEventListener("FidesLocaleUpdated", (evt) => {
  console.log(`Locale: ${evt.detail.locale}`);
  console.log(`Timestamp: ${evt.detail.timestamp}ms`);
});
```

#### Overrides

`CustomEvent.detail`
