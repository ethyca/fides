# FidesJS: JavaScript SDK for Fides

FidesJS is a JavaScript SDK to integrate Fides consent into any website or
app! Commonly referred to as a Consent Management Platform (CMP), FidesJS
includes all the UI components (banners, modals, etc.), state management, and
utility functions you need to collect consent & enforce data privacy in your
application.

For example, FidesJS is used to:
- automatically configure the current user session with the applicable
default consent preferences for their location (e.g. opt-out of data sales,
opt-in to analytics, etc.)
- show a consent UI component (banner, modal, etc.) to the current user with
the applicable privacy notices for them to opt-in, opt-out, etc.
- store the current user's consent preferences in a first-party cookie to
remember their choices in future sessions
- expose the current user's consent preferences via a simple `Fides.consent`
JavaScript API to integrate consent into your own application
- dispatch events on the global `window` (e.g. `FidesUpdated`,
`FidesUIShown`) to easily sync consent changes to your application in
real-time based on the current user's actions
- integrate the current user's consent to other scripts via integrations with
Google Tag Manager, IAB TCF, etc.
- ...and more!

See [Fides](interfaces/Fides.md) for how to use the `window.Fides` JavaScript API, [FidesOptions](interfaces/FidesOptions.md) for supported options to customize it's behavior, and [FidesEvent](interfaces/FidesEvent.md) for how to use `window.addEventListener(...)` to subscribe to
custom Fides events for real-time updates.

## Interfaces

- [FidesEvent](interfaces/FidesEvent.md)
- [FidesExperienceConfig](interfaces/FidesExperienceConfig.md)
- [FidesOptions](interfaces/FidesOptions.md)
- [Fides](interfaces/Fides.md)


## Types

- [PrivacyNoticeRegion](types/PrivacyNoticeRegion.md)  
