import { DEFAULT_FIDES_JS_MAX_AGE_SECONDS } from "~/app/server-utils/loadEnvironmentVariables";

describe("fides.js API route", () => {
  it("returns the fides.js package bundled with the global config", () => {
    cy.request("/fides.js").then((response) => {
      expect(response.status).to.eq(200);
      expect(response)
        .to.have.property("headers")
        .to.have.property("content-type")
        .to.eql("application/javascript");

      // Run a few checks on the "bundled" response body, which should:
      // 1) Be an IIFE that...
      // 2) ...includes a call to Fides.init with a config JSON that...
      // 3) ...is populated with the config.json options
      expect(response.body)
        .to.match(/^\(function/, "should be an IIFE")
        .to.match(/\}\)\(\);\s+$/, "should be an IIFE");
      expect(response.body)
        .to.match(/window.Fides.config = \{/, "should bundle Fides.init")
        .to.match(/Fides.init\(\);/, "should call Fides.init");
      const matches = response.body.match(
        /window.Fides.config = (?<json>\{.*?\});/,
      );
      expect(matches).to.have.nested.property("groups.json");
      expect(JSON.parse(matches.groups.json))
        .to.have.nested.property("consent.options")
        .to.have.length(3);
    });
  });

  it("supports /fides-consent.js route for backwards-compatibility", () => {
    cy.request("/fides-consent.js").then((legacyResponse) => {
      expect(legacyResponse.status).to.eq(200);
      expect(legacyResponse)
        .to.have.property("headers")
        .to.have.property("content-type")
        .to.eql("application/javascript");

      cy.request("/fides.js").then((standardResponse) => {
        expect(standardResponse.body).equals(legacyResponse.body);
      });
    });
  });

  describe("when pre-fetching geolocation", () => {
    it("returns geolocation if provided as a '?geolocation' query param", () => {
      cy.request("/fides.js?geolocation=US-CA").then((response) => {
        expect(response.body).to.match(/window.Fides.config = \{/);
        const matches = response.body.match(
          /window.Fides.config = (?<json>\{.*?\});/,
        );
        expect(JSON.parse(matches.groups.json))
          .to.have.nested.property("geolocation")
          .to.deep.equal({
            location: "US-CA",
            country: "US",
            region: "CA",
          });
      });
    });

    it("returns geolocation if provided as CloudFront geolocation headers", () => {
      cy.request({
        url: "/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "FR",
          "CloudFront-Viewer-Country-Region": "IDF",
        },
      }).then((response) => {
        expect(response.body).to.match(/window.Fides.config = \{/);
        const matches = response.body.match(
          /window.Fides.config = (?<json>\{.*?\});/,
        );
        expect(JSON.parse(matches.groups.json))
          .to.have.nested.property("geolocation")
          .to.deep.equal({
            location: "FR-IDF",
            country: "FR",
            region: "IDF",
          });
      });
    });
  });

  describe("when GPP is forced as a '?gpp' query param", () => {
    it("always returns GPP extension regardless of location", () => {
      cy.request("/fides.js?gpp=true").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?gpp=true&geolocation=US-ID").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?gpp=true&geolocation=US-CA").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?gpp=true&geolocation=FR-IDF").then((response) => {
        expect(response.body).to.match(/window.__gpp/);
      });
      cy.request("/fides.js?geolocation=US-ID").then((response) => {
        expect(response.body).not.to.match(/window.__gpp/);
      });
    });
  });

  it("caches in the browser", () => {
    cy.intercept("/fides.js").as("fidesJS");

    // Load the demo page 3 times, and check /fides.js is called *at most* once
    // NOTE: Depending on browser cache, it might not be called at all - so zero
    // times is a valid number of calls
    cy.visit("/fides-js-demo.html");
    cy.visit("/fides-js-demo.html");
    cy.visit("/fides-js-demo.html");
    cy.get("@fidesJS.all").its("length").should("be.within", 0, 1);
  });

  describe("when generating cache-control headers", () => {
    beforeEach(() => {
      cy.request("/fides.js").then((response) => {
        expect(response.status).to.eq(200);
        cy.wrap(response.headers).as("headers");
        cy.get("@headers").should("have.property", "etag").as("etag");
        cy.get("@headers")
          .should("have.property", "cache-control")
          .as("cacheHeaders");
      });
    });

    it("stores publicly for FIDES_PRIVACY_CENTER__FIDES_JS_MAX_AGE_SECONDS seconds", () => {
      // NOTE: It's not possible to modify the environment variable in the test,
      // so we just check the default value is respected here
      cy.get("@cacheHeaders").should("match", /public/);
      cy.get("@cacheHeaders")
        .invoke("match", /max-age=(?<expiry>\d+)/)
        .its("groups.expiry")
        .then(parseInt)
        .should("equal", DEFAULT_FIDES_JS_MAX_AGE_SECONDS);
    });

    it("generates 'etag' that is consistent when re-requested", () => {
      cy.request("/fides.js")
        .should("have.nested.property", "headers.etag")
        .then((etag) => {
          cy.get("@etag").should("eq", etag);
        });
    });

    it("generates 'etag' that varies based on geolocation query params", () => {
      cy.request("/fides.js?geolocation=US-CA")
        .should("have.nested.property", "headers.etag")
        .as("USCATag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
        });

      // Fetch a second time with a different geolocation param
      cy.request("/fides.js?geolocation=FR")
        .should("have.nested.property", "headers.etag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
          cy.get("@USCATag").should("not.eq", etag);
        });
    });

    it("generates 'etag' that varies based on Cloudfront geolocation headers", () => {
      cy.request({
        url: "/fides.js",
        headers: {
          "Cloudfront-Viewer-Country": "US",
          "Cloudfront-Viewer-Country-Region": "CA",
        },
      })
        .should("have.nested.property", "headers.etag")
        .as("USCATag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
        });

      // Fetch a second time with different geolocation headers
      cy.request({
        url: "/fides.js",
        headers: {
          "Cloudfront-Viewer-Country": "FR",
        },
      })
        .should("have.nested.property", "headers.etag")
        .as("headersTag")
        .then((etag) => {
          cy.get("@etag").should("not.eq", etag);
          cy.get("@USCATag").should("not.eq", etag);
        });
    });

    it("returns 'vary' header for supported Cloudfront geolocation headers", () => {
      const expected = [
        "cloudfront-viewer-country",
        "cloudfront-viewer-country-region",
      ];
      cy.get("@headers")
        .should("have.property", "vary")
        .then((vary: any) => {
          const varyHeaders = (vary as string).replace(" ", "").split(",");
          expect(varyHeaders).to.include.members(expected);
        });
    });
  });

  describe("when disabling initialization", () => {
    it("does not call widnow.Fides.init", () => {
      cy.request("/fides.js?initialize=false").then((response) => {
        expect(response.body).not.to.match(/window.Fides.init(fidesConfig)/);
      });
    });
  });

  describe("when handling multiple script loading", () => {
    it("prevents execution when script is loaded multiple times on the same page", () => {
      cy.visit("/fides-js-demo.html");

      // Wait for initial Fides to load
      cy.window().should("have.property", "Fides");

      // Spy on console.error to capture the warning message
      cy.window().then((win) => {
        cy.spy(win.console, "error").as("consoleError");

        // Inject a second script tag to simulate multiple loading
        const script = win.document.createElement("script");
        script.src = "/fides.js";
        win.document.head.appendChild(script);

        // Wait for script to load and check that error was logged
        cy.get("@consoleError").should("have.been.called");
      });
    });

    it("allows reloading when fides_unsupported_repeated_script_loading is enabled", () => {
      cy.visit(
        "/fides-js-demo.html?fides_unsupported_repeated_script_loading=enabled_acknowledge_not_supported",
      );

      // Wait for initial Fides to load
      cy.window().should("have.property", "Fides");

      cy.window().then((win) => {
        cy.spy(win.console, "error").as("consoleError");

        // Inject a second script tag
        const script = win.document.createElement("script");
        script.src =
          "/fides.js?fides_unsupported_repeated_script_loading=enabled_acknowledge_not_supported";
        win.document.head.appendChild(script);

        // Should NOT log the error message when the option is enabled
        cy.get("@consoleError").should("not.have.been.called");
      });
    });

    it("handles script removal and re-addition scenario", () => {
      cy.visit("/fides-js-demo.html");

      // Wait for initial Fides to load
      cy.window().should("have.property", "Fides");

      cy.window().then((win) => {
        // Store reference to original Fides
        const originalFides = win.Fides;

        // Find and remove the existing fides script tag
        const existingScript = win.document.querySelector(
          'script[src*="/fides.js"]',
        );
        if (existingScript) {
          existingScript.remove();
        }

        cy.spy(win.console, "error").as("consoleError");

        // Add a new script tag (simulating customer removing and re-adding)
        const newScript = win.document.createElement("script");
        newScript.src = "/fides.js";
        win.document.head.appendChild(newScript);

        // Should prevent re-execution since Fides object still exists
        cy.get("@consoleError").should("have.been.called");

        // Verify that the original Fides object is still intact
        expect(win.Fides).to.equal(originalFides);
      });
    });

    it("handles multiple script tags present from page load", () => {
      // Create a custom test page with multiple script tags
      cy.visit("/fides-js-demo.html").then(() => {
        cy.window().then((win) => {
          // Clear the page and add multiple script tags
          win.document.body.innerHTML = `
            <div>
              <h1>Multiple Scripts Test</h1>
              <script src="/fides.js"></script>
              <script src="/fides.js"></script>
            </div>
          `;

          cy.spy(win.console, "error").as("consoleError");

          // Force execution of the scripts by creating new ones
          const script1 = win.document.createElement("script");
          script1.src = "/fides.js";
          const script2 = win.document.createElement("script");
          script2.src = "/fides.js";

          win.document.head.appendChild(script1);

          // Wait a bit then add the second script
          setTimeout(() => {
            win.document.head.appendChild(script2);
          }, 100);

          // The second script should be prevented from executing
          cy.get("@consoleError").should("have.been.called");
        });
      });
    });
  });
});

// Convert this to a module instead of script (allows import/export)
export {};
