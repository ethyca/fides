import { ContainerNode } from "preact";

import { FidesExperienceTranslationOverrides } from "../lib/consent-types";
import type { I18n } from "../lib/i18n";
import { InitializedFidesGlobal } from "../lib/providers/fides-global-context";

/**
 * The type of the parent component for the preact app
 *
 * When using fides.ts to render the preact app, need to use this type!
 * Similarly, when creating different overlay "types", they should all take
 * this type as a prop.
 */
export type RenderOverlayType = (
  props: {
    i18n: I18n;
    initializedFides: InitializedFidesGlobal;
    translationOverrides?: Partial<FidesExperienceTranslationOverrides>;
  },
  parent: ContainerNode,
) => void;
