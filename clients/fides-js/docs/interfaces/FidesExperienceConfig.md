# Interface: FidesExperienceConfig

In addition to the base functionality code, the FidesJS script will automatically
determine which experience to provide the end user by matching configured privacy
notices, locations, and languages to the user's session.

You can access the properties of the config used to provide the user's experience
in the [Fides](Fides.md) global object at `Fides.experience.experience_config` which may be
useful in further customizing the user's experience within your own environment
(e.g. `if (Fides.experience.experience_config.component==='banner_and_modal') {...}`).
See the list of reliable properties below for details.

NOTE: FidesJS will need to be downloaded, executed, and initialized before
the `Fides` object is available. Therefore, your code should check for the
existence of Fides *or* subscribe to the global `FidesInitialized` event (see
[FidesEvent](FidesEvent.md)) for details) before using the `Fides` object in your own code.

## Properties

### auto\_detect\_language?

> `optional` **auto\_detect\_language**: `boolean`

This property corresponds with the "Auto detect language" configuration toggle in the Privacy experience config

***

### auto\_subdomain\_cookie\_deletion?

> `optional` **auto\_subdomain\_cookie\_deletion**: `boolean`

This property corresponds with the "Automatically delete subdomain cookies" option.

***

### component

> **component**: `string`

Each configured experience is presented to the user as one of 4 types of components: `"banner_and_modal"`, `"modal"`, `"privacy_center"`, or `"tcf_overlay"`. This property corresponds with the current user's Experience type.

***

### dismissable?

> `optional` **dismissable**: `boolean`

This property corresponds with the "Allow user to dismiss"
configuration toggle. If disabled, it will return `false` and the "X"
button in the upper right corner of the banner/modal will be removed.

***

### id

> **id**: `string`

Every configured experience has a unique ID that can be used to
distinguish it from other experiences.

***

### layer1\_button\_options?

> `optional` **layer1\_button\_options**: `string`

This property corresponds with the "Banner options" in the Banner
and Modal components. This helps determine which buttons are visible
on the banner presented to the user. (e.g. `"acknowledge"` or `"opt_in_opt_out"`)

***

### name?

> `optional` **name**: `string`

Full name of the configured experience (e.g. `"US Modal"`)

***

### regions?

> `optional` **regions**: [PrivacyNoticeRegion](../types/PrivacyNoticeRegion)[]

List of [region codes](../types/PrivacyNoticeRegion) that apply.

#### Example

```ts
[ "us_ca", "us_co", "us_ct", "us_ut", "us_va", "us_or", "us_tx" ]
```

***

### show\_layer1\_notices?

> `optional` **show\_layer1\_notices**: `boolean`

On Banner and Modal components, this option corresponds to the "Add privacy notices to banner" configuration toggle. When enabled, the list of privacy notice names will appear&mdash;comma separated&mdash;on the banner, without forcing the user to open the modal to know which are applicable.

***

### translations

> **translations**: `Record`\<`string`, `any`\>[]

List of all available translations for the current experience.
