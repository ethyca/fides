import { ContainerNode } from "preact";

import type {
  FidesConfig,
  FidesCookie,
  FidesExperienceTranslationOverrides,
  FidesGlobal,
  FidesInitOptions,
  NoticeConsent,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../lib/consent-types";
import type { I18n } from "../lib/i18n";

/**
 * The type of the parent component for the preact app
 *
 * When using fides.ts to render the preact app, need to use this type!
 * Similarly, when creating different overlay "types", they should all take
 * this type as a prop.
 */
export interface OverlayProps {
  options: FidesInitOptions;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  cookie: FidesCookie;
  fidesRegionString: string;
  savedConsent: NoticeConsent;
  translationOverrides?: Partial<FidesExperienceTranslationOverrides>;
}

export type RenderOverlayType = (
  props: OverlayProps & {
    i18n: I18n;
    initializedFides: InitializedFidesGlobal;
  },
  parent: ContainerNode,
) => void;

export interface InitializedFidesGlobal extends FidesGlobal {
  cookie: FidesCookie;
  config: FidesConfig;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  fidesRegionString: string;
}
