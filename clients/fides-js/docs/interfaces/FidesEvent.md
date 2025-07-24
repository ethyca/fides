# Interface: FidesEvent

FidesJS dispatches a variety of lifecyle events to the global `window`,
making it easy to subscribe to an event stream to keep your application
updated in real-time. Each of these events extends the standard
[CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)
interface and include a [detail](FidesEvent.md#detail) object with various properties that
can be used for inspecting current consent preferences, generating analytics,
etc.

## Example

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

- `FidesInitializing`: Dispatched when initialization begins, which happens
immediately once the FidesJS script is loaded. If `Fides.init()` is called
multiple times, this event will also be dispatched each time.

- `FidesConsentLoaded`: If previously saved consent was found during initialization,
we immediately set it on the `Fides` global object and dispatch this event.
This event will only be dispatched if consent was found.

- `FidesReady`: Dispatched when initialization is complete and the
current user's consent preferences - either previously saved or applicable
defaults - have been set on the `Fides` global object.
This event will always be dispatched, even if no previous consent was found.

- `FidesInitialized`: This event is dispatched based on the `fidesInitializedEventMode` setting:
  - "once" (default): fires alongside `FidesReady` only
  - "multiple": fires alongside both `FidesReady` and `FidesConsentLoaded` events
  - "disable": never fires
For new projects, we strongly encourage using `FidesReady` and `FidesConsentLoaded` instead.

- `FidesUpdating`: Dispatched when a user action (e.g. accepting all, saving
changes, applying GPC) has started updating the user's consent preferences.
This event is dispatched immediately once the changes are made, but before
they are saved to the `Fides` object, `fides_consent` cookie on the user's
device, and the Fides API. To wait until the changes are fully
applied, use the `FidesUpdated` event instead.

- `FidesUpdated`: Dispatched when a user action (e.g. accepting all, saving
changes, applying GPC) has finished updating the user's consent preferences.
This event is dispatched once the changes are fully saved to the `Fides`
object, `fides_consent` cookie on the user's device, and the Fides API. To
receive an event that fires before these changes are saved, use the
`FidesUpdating` event instead.

- `FidesUIShown`: Dispatched whenever a FidesJS UI component is rendered and
shown to the current user (banner, modal, etc.). The specific component shown
can be obtained from the `detail.extraDetails.servingComponent` property on
the event.

- `FidesUIChanged`: Dispatched whenever the current user changes their
preferences in the FidesJS UI but has yet to *save* those changes (i.e.
"dirty").

- `FidesModalClosed`: Dispatched whenever the FidesJS modal is closed.

**Note**: The events `FidesUIShown`, `FidesUIChanged`, and `FidesModalClosed` are not available in a Headless experience, as they are specific to the FidesJS UI components.

## Extends

- `CustomEvent`

## Properties

### detail

> **detail**: `object`

Event properties passed by FidesJS when dispatched. Depending on the event type, some properties may or may not be set, so most of these are marked as optional.

#### consent

> **consent**: `Record`\<`string`, `boolean`\>

User's current consent preferences; see [Fides.consent](Fides.md#consent) for detail.

#### fides\_string?

> `optional` **fides\_string**: `string`

User's current consent string; see [Fides.fides_string](Fides.md#fides_string) for detail.

#### timestamp?

> `optional` **timestamp**: `number`

High-precision timestamp from [performance.mark()](https://developer.mozilla.org/en-US/docs/Web/API/Performance/mark)
representing when this event was created. The timestamp is measured in milliseconds since page load.

May be undefined if the Performance API is not available.

#### extraDetails?

> `optional` **extraDetails**: `object`

Extra event properties, for additional context.

#### extraDetails.servingComponent?

> `optional` **servingComponent**: `"banner"` \| `"modal"` \| `"tcf_banner"` \| `"tcf_overlay"`

Which FidesJS UI component (if any) caused this event.

#### extraDetails.shouldShowExperience?

> `optional` **shouldShowExperience**: `boolean`

Whether the user should be shown the consent experience. Only available on FidesConsentLoaded and FidesReady events.

#### extraDetails.consentMethod?

> `optional` **consentMethod**: `"accept"` \| `"reject"` \| `"save"` \| `"dismiss"` \| `"acknowledge"` \| `"gpc"` \| `"script"` \| `"ot_migration"`

What consent method (if any) caused this event.

#### extraDetails.trigger?

> `optional` **trigger**: `object`

What UI element (if any) triggered this event, as well as the origin of
the event.

#### extraDetails.trigger.origin?

> `optional` **origin**: `"fides"` \| `"external"`

Where the event originated from. If the event was triggered using an
SDK script, for example, this will be "external", meaning the event
was triggered by something other than a FidesJS UI element.

#### extraDetails.trigger.type?

> `optional` **type**: `"toggle"` \| `"button"` \| `"link"`

The type of element that triggered the event. Additional types may be
added over time, so expect this type to grow.
Only present when origin is "fides".

#### extraDetails.trigger.label?

> `optional` **label**: `string`

The UI label of the element that triggered the event.

#### extraDetails.trigger.checked?

> `optional` **checked**: `boolean`

The checked state of the element that triggered the event.
Only present when type is "toggle".

#### extraDetails.preference?

> `optional` **preference**: `object`

Information about the specific preference being changed, if this event
was triggered by a preference change.

##### Example

```ts
// For a notice toggle:
preference: {
  key: "advertising",
  type: "notice"
}

// For a TCF purpose toggle:
preference: {
  key: "tcf_purpose_consent_4",
  type: "tcf_purpose_consent"
}

// For a TCF vendor toggle:
preference: {
  key: "gvl.2",
  type: "tcf_vendor_consent",
  vendor_id: "gvl.2",
  vendor_list: "gvl",
  vendor_list_id: "2",
  vendor_name: "Captify"
}
```

#### extraDetails.preference.key

> **key**: `string`

The unique key identifying this preference

#### extraDetails.preference.type

> **type**: `"notice"` \| `"tcf_purpose_consent"` \| `"tcf_purpose_legitimate_interest"` \| `"tcf_special_feature"` \| `"tcf_vendor_consent"` \| `"tcf_vendor_legitimate_interest"`

The type of preference being changed

#### extraDetails.preference.vendor\_id?

> `optional` **vendor\_id**: `string`

The vendor ID if this is a vendor-related preference

#### extraDetails.preference.vendor\_list?

> `optional` **vendor\_list**: `"gvl"` \| `"gacp"` \| `"fds"`

The vendor list type if this is a vendor-related preference

#### extraDetails.preference.vendor\_list\_id?

> `optional` **vendor\_list\_id**: `string`

The vendor list ID if this is a vendor-related preference

#### extraDetails.preference.vendor\_name?

> `optional` **vendor\_name**: `string`

The vendor name if this is a vendor-related preference

#### Example

```ts
window.addEventListener("FidesUpdated", (evt) => {
  if (evt.detail.extraDetails?.consentMethod === "accept") {
    console.log("Current user clicked the 'Accept' button!");
  }
});
```

#### Overrides

`CustomEvent.detail`
