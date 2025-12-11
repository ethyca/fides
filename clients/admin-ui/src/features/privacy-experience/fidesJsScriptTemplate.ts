import { Property } from "~/types/api";

export const PRIVACY_CENTER_HOSTNAME_TEMPLATE = "{privacy-center-hostname-and-path}";
// export const PROPERTY_UNIQUE_ID_TEMPLATE = "{property-unique-id}";

/**
 * Generates the property ID query parameter string for the Fides.js script URL
 */
const PROPERTY_UNIQUE_ID_TEMPLATE = (propertyId?: string | null): string => {
    if (propertyId) {
        return propertyId;
    }
    return "{property-unique-id}";
};
/**
 * Generates the complete Fides.js script tag with privacy center hostname and property ID
 */
export const FIDES_JS_SCRIPT_TEMPLATE = (privacyCenterHostname?: string, property?: Property): string => {
    const propertyId = property?.id;
    const propertyIdDeclaration = propertyId ? `var fidesPropertyId = "${PROPERTY_UNIQUE_ID_TEMPLATE(propertyId)}"; // Example Property ID\n    ` : "";
    const propertyIdQueryParam = propertyId ? ` + "property_id=" + fidesPropertyId` : "";

    let script = `<script>
(function () {
    var fidesHost = "${PRIVACY_CENTER_HOSTNAME_TEMPLATE}"; // This should be the CDN url.
    ${propertyIdDeclaration}var fidesSrc = fidesHost + "/fides.js?"${propertyIdQueryParam};

    function insertFidesScript() {
        addEventListener("FidesInitializing", function () {
            // any pre-initialization code can go here
            // window.Fides.gtm();
        });

        addEventListener("FidesInitialized", function () {
            // addExperienceIdToBody();
        });

        function addExperienceIdToBody() {
            try {
                var experience = window.Fides.experience || {};
                var config = experience.experience_config || {};
                var id = config.id;
                if (id) {
                    window.document.body.classList.add(id);
                }
            } catch {
                console.warn("Couldn't apply Fides experience ID to body.");
            }
        }

        var fidesPrefix = "fides_";
        var searchParams = new URLSearchParams(location.search);
        var fidesSearchParams = new URLSearchParams();
        searchParams.forEach(function (value, key) {
            if (key.startsWith(fidesPrefix)) {
                fidesSearchParams.set(
                    key.replace(fidesPrefix, ""),
                    key === fidesPrefix + "cache_bust" ? Date.now().toString() + "&refresh=true" : value
                );
            }
        });

        var src = fidesSrc + fidesSearchParams.toString();
        var script = document.createElement("script");
        script.async = false;
        script.defer = false;
        script.setAttribute("src", src);
        script.setAttribute("id", "fides-js");
        script.setAttribute("type", "text/javascript");
        document.head.appendChild(script);
    }

    insertFidesScript();
})();
</script>`;

    // Replace privacy center hostname template if provided
    if (privacyCenterHostname) {
        script = script.replaceAll(PRIVACY_CENTER_HOSTNAME_TEMPLATE, privacyCenterHostname);
    }

    // // Replace property ID template if provided
    // if (propertyId) {
    //     script = script.replaceAll(PROPERTY_UNIQUE_ID_TEMPLATE, propertyId);
    // }

    return script;
};
