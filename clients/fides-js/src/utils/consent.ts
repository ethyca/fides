import {UserGeolocation} from "~/lib/consent-types";
import {debugLog} from "~/lib/consent-utils";

/**
 * Construct user geolocation str to be ingested by Fides API
 * Returns null if geolocation cannot be constructed by provided params
 */
export const constructLocation = (
    geoLocation?: UserGeolocation,
    debug: boolean = false
): string | null => {
    debugLog(debug, "constructing geolocation...");
    if (!geoLocation) {
        debugLog(
            debug,
            "cannot construct user location since geoLocation is undefined"
        );
        return null;
    }
    if (geoLocation.location) {
        return geoLocation.location;
    }
    if (geoLocation.country && geoLocation.region) {
        return `${geoLocation.country}-${geoLocation.region}`;
    }
    if (geoLocation.country) {
        return geoLocation.country;
    }
    debugLog(
        debug,
        "cannot construct user location from provided geoLocation params..."
    );
    return null;
};