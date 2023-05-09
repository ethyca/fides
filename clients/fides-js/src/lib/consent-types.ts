export type ConsentBannerOptions = {
  // Whether or not debug log statements should be enabled
  debug?: boolean;

  // Whether or not the banner should be globally disabled
  isDisabled?: boolean;

  // Whether user geolocation should be enabled. Requires geolocationApiUrl
  isGeolocationEnabled?: boolean;

  // API URL for getting user geolocation
  geolocationApiUrl?: string;

  // Display labels used for the banner text
  labels?: {
    bannerDescription?: string;
    primaryButton?: string;
    secondaryButton?: string;
    tertiaryButton?: string;
  };

  // URL for the Privacy Center, used to customize consent preferences. Required.
  privacyCenterUrl?: string;
};

export type UserGeolocation = {
  country?: string; // "US"
  ip?: string; // "192.168.0.1:12345"
  location?: string; // "US-NY"
  region?: string; // "NY"
};

export enum ButtonType {
  PRIMARY = "primary",
  SECONDARY = "secondary",
  TERTIARY = "tertiary"
}