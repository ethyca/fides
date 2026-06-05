import { DictOption } from "~/features/plus/plus.slice";

/**
 * Dev-only mock Fides Compass vendors.
 *
 * The local backend's dictionary/compass service is disabled (`dictionary
 * .enabled = false`) and real vendors are proxied from an external Compass
 * service with no local table to seed. These stand-ins let the Add-System
 * "Search Fides Compass" path be seen and exercised locally when no real
 * Compass service is available. Each `value` is the vendor_id stamped onto the
 * created system to mark it as compass-sourced (the `compass.` prefix is what
 * `extractVendorSource` classifies as a Compass vendor).
 */
export const MOCK_COMPASS_VENDORS: DictOption[] = [
  {
    label: "Google Analytics",
    value: "compass.google-analytics",
    description:
      "Web analytics service that tracks and reports website traffic and user behavior.",
  },
  {
    label: "Stripe",
    value: "compass.stripe",
    description:
      "Payment processing platform for online and in-person transactions.",
  },
  {
    label: "Intercom",
    value: "compass.intercom",
    description:
      "Customer messaging platform for support, engagement, and marketing.",
  },
  {
    label: "HubSpot",
    value: "compass.hubspot",
    description:
      "CRM platform with marketing, sales, and customer service software.",
  },
  {
    label: "Meta Pixel",
    value: "compass.meta-pixel",
    description:
      "Analytics tool that measures the effectiveness of advertising on Meta platforms.",
  },
  {
    label: "Zendesk",
    value: "compass.zendesk",
    description: "Customer service and support ticketing platform.",
  },
];
