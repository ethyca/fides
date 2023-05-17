import {debugLog} from "~/lib/consent-utils";
import {PrivacyExperience} from "~/lib/consent-types";

/**
 * Fetch the relevant experience based on user location and user device id (if exists)
 */
export const getExperience = (userLocationString: String, debug: boolean): PrivacyExperience | undefined => {
    debugLog(
        debug,
        "Fetching experience where component === privacy_center...",
        userLocationString
    );
    // TODO: implement
    return undefined;
}