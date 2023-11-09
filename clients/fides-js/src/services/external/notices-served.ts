import {
  FidesOptions,
  LastServedConsentSchema,
  RecordConsentServedRequest,
} from "../../lib/consent-types";

import { debugLog } from "../../lib/consent-utils";

/**
 * Helper function to save notices served to an external API
 */
export async function customPatchNoticesServed(
  options: FidesOptions,
  request: RecordConsentServedRequest
): Promise<Array<LastServedConsentSchema> | null> {
  if (!options.apiOptions?.patchNoticesServedFn) {
    return null;
  }
  debugLog(options.debug, "Calling patch notices served fn");
  try {
    return await options.apiOptions.patchNoticesServedFn(request);
  } catch (e) {
    debugLog(
      options.debug,
      "Error patching notices served to custom API, continuing. Error: ",
      e
    );
    return null;
  }
}
