import { ConsentMethod } from "~/types/api";

/**
 * Settings that can be controlled using ENV vars on the server.
 *
 * Any of these can be set by adding the prefix "FIDES_PRIVACY_CENTER__", e.g.
 *
 * FIDES_PRIVACY_CENTER__FIDES_API_URL=https://fides.example.com/api/v1
 */
export interface PrivacyCenterSettings {
  // Privacy center settings
  FIDES_API_URL: string; // e.g. http://localhost:8080/api/v1
  SERVER_SIDE_FIDES_API_URL: string | null; // e.g. http://fides:8080/api/v1
  CONFIG_CSS_URL: string; // e.g. file:///app/config/config.css
  CONFIG_JSON_URL: string; // e.g. file:///app/config/config.json
  SHOW_BRAND_LINK: boolean; // whether to render the Ethyca brand link
  CUSTOM_PROPERTIES: boolean; // (optional) (default: true) enables the use of a single privacy center instance to serve different properties on different paths with custom configs
  FIDES_PRIVACY_CENTER__ROOT_PROPERTY_PATH: string | null; // (optional) setting this will fetch a property when navigating the root ("/") path.

  // Fides.js options
  DEBUG: boolean; // whether console logs are enabled for consent components
  GEOLOCATION_API_URL: string; // e.g. http://location-cdn.com
  IS_GEOLOCATION_ENABLED: boolean; // whether we should use geolocation to drive privacy experience
  IS_OVERLAY_ENABLED: boolean; // whether we should render privacy-experience-driven components
  IS_PREFETCH_ENABLED: boolean | false; // (optional) whether we should pre-fetch geolocation and experience server-side
  OVERLAY_PARENT_ID: string | null; // (optional) ID of the parent DOM element where the overlay should be inserted
  MODAL_LINK_ID: string | null; // (optional) ID of the DOM element that should trigger the consent modal
  PRIVACY_CENTER_URL: string; // e.g. http://localhost:3001
  FIDES_EMBED: boolean | false; // (optional) Whether we should "embed" the fides.js overlay UI (ie. “Layer 2”) into a web page
  FIDES_DISABLE_SAVE_API: boolean | false; // (optional) Whether we should disable saving consent preferences to the Fides API
  FIDES_DISABLE_NOTICES_SERVED_API: boolean | false; // (optional) Whether we should only disable saving notices served to the Fides API
  FIDES_DISABLE_BANNER: boolean | false; // (optional) Whether we should disable showing the banner
  FIDES_TCF_GDPR_APPLIES: boolean; // (optional) The default for the TCF GDPR applies value (default true)
  FIDES_STRING: string | null; // (optional) An explicitly passed-in string that supersedes the cookie. Can contain both TC and AC strings
  IS_FORCED_TCF: boolean; // whether to force the privacy center to use the fides-tcf.js bundle
  FIDES_JS_BASE_URL: string; // A base URL to a directory of fides.js scripts
  CUSTOM_OPTIONS_PATH: string | null; // (optional) A custom path to fetch FidesOptions (e.g. "window.config.overrides"). Defaults to window.fides_overrides
  PREVENT_DISMISSAL: boolean; // whether or not the user is allowed to dismiss the banner/overlay
  ALLOW_HTML_DESCRIPTION: boolean | null; // (optional) whether or not HTML descriptions should be rendered
  BASE_64_COOKIE: boolean; // whether or not to encode cookie as base64 on top of the default JSON string
  FIDES_PRIMARY_COLOR: string | null; // (optional) sets fides primary color
  FIDES_CLEAR_COOKIE: boolean; // (optional) deletes fides_consent cookie on reload
  FIDES_CONSENT_OVERRIDE: ConsentMethod.ACCEPT | ConsentMethod.REJECT | null; // (optional) sets a previously learned consent preference for the user
}
