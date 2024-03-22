# Interface: FidesEvent

FidesJS dispatches a variety of lifecyle events to the global `window`,
making it easy to subscribe to an event stream to keep your application
updated in real-time. Each of these events extends the standard
[CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)
interface and include a [detail](FidesEvent.md#detail) object with various properties that
can be used for inspecting current consent preferences, generating analytics,
etc.

**`Example`**

```ts
window.addEventListener("FidesUpdated", (evt) => {
  console.log("Received 'FidesUpdated' event! Current consent preferences: ", evt.detail.consent);
});
```

See the list below for information on what events are dispatched (and when!)
and the [detail](FidesEvent.md#detail) reference for the available properties.

For more information on working with these kind of `CustomEvent` objects in
the browser, see the MDN docs:
[https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)

### List of FidesEvent Types

- `FidesInitialized`: Dispatched when initialization is complete and the
current user's consent preferences - either previously saved or applicable
defaults - have been set on the `Fides` global object.

- `FidesUpdated`: Dispatched whenever the current user's consent preferences
are updated on the `Fides` global object due to a user action (e.g. accepting
all, applying GPC). The

- `FidesUIShown`: Dispatched whenever a FidesJS UI component is rendered and
shown to the current user (banner, modal, etc.). The specific component shown
can be obtained from the `detail.extraDetails.servingComponent` property on
the event.

- `FidesUIChanged`: Dispatched whenever the current user changes their
preferences in the FidesJS UI but has yet to *save* those changes (i.e.
"dirty").

- `FidesModalClosed`: Dispatched whenever the FidesJS modal is closed.

## Hierarchy

- `CustomEvent`

  ↳ **`FidesEvent`**

## Table of contents

### Properties

- [detail](FidesEvent.md#detail)

## Properties

### detail

• **detail**: `Object`

Event properties passed by FidesJS when dispatched. Depending on the event type, some properties may or may not be set, so most of these are marked as optional.

**`Example`**

```ts
window.addEventListener("FidesUpdated", (evt) => {
  if (evt.detail.extraDetails?.consentMethod == "accept") {
    console.log("Current user clicked the 'Accept' button!");
  }
});
```

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `consent` | `Record`\<`string`, `boolean`\> | User's current consent preferences; see [Fides.consent](Fides.md#consent) for detail. |
| `fides_string?` | `string` | User's current consent string; see [Fides.fides_string](Fides.md#fides_string) for detail. |
| `extraDetails?` | \{ `servingComponent?`: ``"banner"`` \| ``"modal"`` \| ``"tcf_banner"`` \| ``"tcf_overlay"`` ; `consentMethod?`: ``"dismiss"`` \| ``"accept"`` \| ``"reject"`` \| ``"save"`` \| ``"gpc"``  } | Extra event properties, for additional context. |
| `extraDetails.servingComponent?` | ``"banner"`` \| ``"modal"`` \| ``"tcf_banner"`` \| ``"tcf_overlay"`` | Which FidesJS UI component (if any) caused this event. |
| `extraDetails.consentMethod?` | ``"dismiss"`` \| ``"accept"`` \| ``"reject"`` \| ``"save"`` \| ``"gpc"`` | What consent method (if any) caused this event. |

#### Overrides

CustomEvent.detail
