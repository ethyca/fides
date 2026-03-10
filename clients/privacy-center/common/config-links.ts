import { PrivacyCenterLink } from "~/types/config";

type ConfigWithLinks = {
  links?: Array<{ label: string; url: string }>;
  privacy_policy_url?: string | null;
  privacy_policy_url_text?: string | null;
};

/**
 * Returns the list of policy links to display, resolving both the new `links`
 * field and the deprecated `privacy_policy_url` / `privacy_policy_url_text`
 * fields for backwards compatibility.
 *
 * Resolution order:
 * 1. If `links` is non-empty, use it.
 * 2. If the deprecated fields are both present, synthesize a single-item list.
 * 3. Otherwise return an empty array.
 */
export const getEffectivePrivacyCenterLinks = (config: ConfigWithLinks): PrivacyCenterLink[] => {
  if (config.links && config.links.length > 0) {
    return config.links;
  }
  if (config.privacy_policy_url && config.privacy_policy_url_text) {
    return [{ url: config.privacy_policy_url, label: config.privacy_policy_url_text }];
  }
  return [];
};
