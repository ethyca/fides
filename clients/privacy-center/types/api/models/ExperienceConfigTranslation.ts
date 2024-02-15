export type ExperienceConfigTranslation = {
  language: string;
  /**
   * Whether the given ExperienceConfigTranslation is a global default
   */
  is_default?: boolean;
  /**
   * Overlay 'Accept button displayed on the Banner and Privacy Preferences' or Privacy Center 'Confirmation button label'
   */
  accept_button_label?: string;
  /**
   * Overlay 'Acknowledge button label for notice only banner'
   */
  acknowledge_button_label?: string;
  banner_description?: string;
  /**
   * Overlay 'Banner Description' or Privacy Center 'Description'
   */
  description?: string;
  banner_title?: string;
  /**
   * Overlay 'Banner title' or Privacy Center 'title'
   */
  title?: string;
  /**
   * Overlay and Privacy Center 'Privacy policy link label'
   */
  privacy_policy_link_label?: string;
  /**
   * Overlay and Privacy Center 'Privacy policy URl'
   */
  privacy_policy_url?: string;
  /**
   * Overlay 'Privacy preferences link label'
   */
  privacy_preferences_link_label?: string;
  /**
   * Overlay 'Reject button displayed on the Banner and 'Privacy Preferences' of Privacy Center 'Reject button label'
   */
  reject_button_label?: string;
  /**
   * Overlay 'Privacy preferences 'Save' button label
   */
  save_button_label?: string;

  experience_config_history_id: string;
  version: number;
};
