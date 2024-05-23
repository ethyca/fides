/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentConfigButton } from "./ConsentConfigButton";
import type { ConsentConfigPage } from "./ConsentConfigPage";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type fides__api__schemas__privacy_center_config__ConsentConfig = {
  button: ConsentConfigButton;
  page: ConsentConfigPage;
};
