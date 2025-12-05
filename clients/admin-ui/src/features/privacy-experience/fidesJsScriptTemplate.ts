export const PRIVACY_CENTER_HOSTNAME_TEMPLATE = "{privacy-center-hostname-and-path}";
export const PROPERTY_UNIQUE_ID_TEMPLATE = "{property-unique-id}";

export const FIDES_JS_SCRIPT_TEMPLATE = `<script>
!(function () {

  var hostPrivacyCenter = "${PRIVACY_CENTER_HOSTNAME_TEMPLATE}";

    // Recommended: Fides override settings
    window.fides_overrides = {
      fides_consent_non_applicable_flag_mode: "include",
      fides_consent_flag_type: "boolean",
    };

    // Optional: Initialize integrations like Google Tag Manager or BlueConic
    addEventListener("FidesInitialized", function () {
      // Fides.gtm();
      // Fides.blueconic();
    });

    // Recommended: wrapper script that allows for dynamic switching of geolocation by adding query params to the window URL
    // query param prefix is "fides_"
    // eg, "fides_geolocation=US-CA"
    var fidesPrefix = "fides_";
    var searchParams = new URLSearchParams(location.search);
    var fidesSearchParams = new URLSearchParams();
    searchParams.forEach(function (value, key) {
      if (key.startsWith(fidesPrefix)) {
        fidesSearchParams.set(
          key.replace(fidesPrefix, ""),
          key === fidesPrefix + "cache_bust" ? Date.now().toString() : value,
        );
      }
    });

    // Required: core Fides JS script
    var src = "https://${PRIVACY_CENTER_HOSTNAME_TEMPLATE}/fides.js?property_id=${PROPERTY_UNIQUE_ID_TEMPLATE}" + fidesSearchParams.toString();
    var script = document.createElement("script");
    script.setAttribute("src", src);
    document.head.appendChild(script);
  })();
</script>`;
