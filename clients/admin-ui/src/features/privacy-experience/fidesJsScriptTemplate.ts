export const removePropertyIdFromScript = (script: string, hasPropertyId: boolean) => {
    if (!hasPropertyId) {
        script = script.replaceAll('+ "?property_id=" + fidesPropertyId + "&"', "");
    }
    return script;
};

export const PRIVACY_CENTER_HOSTNAME_TEMPLATE = "{privacy-center-hostname-and-path}";
export const PROPERTY_UNIQUE_ID_TEMPLATE = "{property-unique-id}";
export const FIDES_JS_SCRIPT_TEMPLATE = `<script>
(function () {
    var fidesHost = "${PRIVACY_CENTER_HOSTNAME_TEMPLATE}"; // This should be the CDN url.
    var fidesPropertyId = "${PROPERTY_UNIQUE_ID_TEMPLATE})"; // Example Property ID
    var fidesSrc = fidesHost + "/fides.js" + "?property_id=" + fidesPropertyId + "&";

    function insertFidesScript() {
        addEventListener("FidesInitializing", function () {
            // any pre-initialization code can go here
            // window.Fides.gtm();
        });

        addEventListener("FidesInitialized", function () {
            // support custom css hackery
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
                    key === fidesPrefix + "cache_bust" ? Date.now().toString() : value
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
