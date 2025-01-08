/**
 * In addition to the base functionality code, the FidesJS script will automatically
 * determine which experience to provide the end user by matching configured privacy
 * notices, locations, and languages to the user's session.
 *
 * You can access the properties of the config used to provide the user's experience
 * in the {@link Fides} global object at `Fides.experience.experience_config` which may be
 * useful in further customizing the user's experience within your own environment
 * (e.g. `if (Fides.experience.experience_config.component==='banner_and_modal') {...}`).
 * See the list of reliable properties below for details.
 *
 * NOTE: FidesJS will need to be downloaded, executed, and initialized before
 * the `Fides` object is available. Therefore, your code should check for the
 * existence of Fides *or* subscribe to the global `FidesInitialized` event (see
 * {@link FidesEvent}) for details) before using the `Fides` object in your own code.
 *
 */
export interface FidesExperienceConfig {
  /**
   * This property corresponds with the "Auto detect language" configuration toggle in the Privacy experience config
   */
  auto_detect_language?: boolean;

  /**
   * This property corresponds with the "Automatically delete subdomain cookies" option.
   */
  auto_subdomain_cookie_deletion?: boolean;

  /**
   * Each configured experience is presented to the user as one of 4 types of components: `"banner_and_modal"`, `"modal"`, `"privacy_center"`, or `"tcf_overlay"`. This property corresponds with the current user's Experience type.
   */
  component: string;

  /**
   * This property corresponds with the "Allow user to dismiss"
   * configuration toggle. If disabled, it will return `false` and the "X"
   * button in the upper right corner of the banner/modal will be removed.
   */
  dismissable?: boolean;

  /**
   * Every configured experience has a unique ID that can be used to
   * distinguish it from other experiences.
   */
  id: string;

  /**
   * This property corresponds with the "Banner options" in the Banner
   * and Modal components. This helps determine which buttons are visible
   * on the banner presented to the user. (e.g. `"acknowledge"` or `"opt_in_opt_out"`)
   */
  layer1_button_options?: string;

  /**
   * Full name of the configured experience (e.g. `"US Modal"`)
   */
  name?: string;

  /**
   * List of region codes that apply.
   * For more information on valid values see {@link PrivacyNoticeRegion}
   * @example
   * ```ts
   * [ "us_ca", "us_co", "us_ct", "us_ut", "us_va", "us_or", "us_tx" ]
   * ```
   */
  regions?: Array<string>;

  /**
   * On Banner and Modal components, this option corresponds to the "Add privacy notices to banner" configuration toggle. When enabled, the list of privacy notice names will appear&mdash;comma separated&mdash;on the banner, without forcing the user to open the modal to know which are applicable.
   */
  show_layer1_notices?: boolean;

  /**
   * List of all available translations for the current experience.
   */
  translations: Array<Record<string, any>>;

  /**
   * @internal
   */
  disabled?: boolean;
  /**
   * @internal
   */
  created_at: string;
  /**
   * @internal
   */
  updated_at: string;
}
