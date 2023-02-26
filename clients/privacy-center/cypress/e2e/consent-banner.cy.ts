import { ConsentBannerOptions } from "fides-consent";

// The fides-consent-demo.html page is wired up to inject the
// `fidesConsentBannerOptions` into the Fides.banner(...) function
declare global {
  interface Window {
    fidesConsentBannerOptions?: ConsentBannerOptions;
  }
}

describe("Consent banner", () => {
    // Default options to use for all tests
    const testBannerOptions: ConsentBannerOptions = {
        debug: true, // enable debug logging
        labels: {
            bannerDescription: "This test website is overriding the banner description label. It is very long, so it'll force a wrap.",
            primaryButton: "Accept Test Cookies",
            secondaryButton: "Reject Test Cookies",
            tertiaryButton: "Manage Test Cookies",
        }
    };

    describe("when disabled", () => {
        beforeEach(() =>{
            cy.visit("/fides-consent-demo.html", {
                onBeforeLoad: (win) => {
                    win.fidesConsentBannerOptions = {
                        ...testBannerOptions,
                        ...{
                            isEnabled: false,
                        }
                    }
                },
            });
        });

        it("does not render", () => {
            cy.get("div#fides-consent-banner").should("not.exist");
            cy.contains("button", "Accept Test Cookies").should("not.exist");
        });
    })

    describe("when enabled", () => {
        beforeEach(() =>{
            cy.visit("/fides-consent-demo.html", {
                onBeforeLoad: (win) => {
                    win.fidesConsentBannerOptions = {
                        ...testBannerOptions,
                        ...{
                            isEnabled: true,
                        }
                    }
                },
            });
        });

        it("should render the expected HTML banner", () => {
            // Consider me paranoid, but the various DOM APIs that consent-banner.ts uses
            // (like createElement) are very easy to mess up. This test is (almost) a DOM
            // snapshot test that asserts that the rendered banner HTML is similar to this:
            //
            // <div id='fides-consent-banner' class='fides-consent-banner'>
            //   <div id='fides-consent-banner-description' class='fides-consent-banner-description'>
            //     {labels.bannerDescription}
            //   </div>
            //   <div id='fides-consent-banner-buttons' class='fides-consent-banner-buttons'>
            //     <button id='fides-consent-banner-tertiary-button' class='fides-consent-banner-button fides-consent-banner-primary-button'>
            //       {labels.tertiaryButton}
            //     </button>
            //     <button id='fides-consent-banner-secondary-button' class='fides-consent-banner-button fides-consent-banner-secondary-button'>
            //       {labels.secondaryButton}
            //     </button>
            //     <button id='fides-consent-banner-primary-button' class='fides-consent-banner-button fides-consent-banner-primary-button'>
            //       {labels.primaryButton}
            //     </button>
            //   </div>
            // </div>
            cy.get("div#fides-consent-banner.fides-consent-banner").within(banner => {
                cy.get("div#fides-consent-banner-description.fides-consent-banner-description")
                  .contains("This test website is overriding the banner description label.");
                cy.get("div#fides-consent-banner-buttons.fides-consent-banner-buttons").within(buttonsDiv => {
                    cy.get("button#fides-consent-banner-button-tertiary.fides-consent-banner-button.fides-consent-banner-button-tertiary")
                      .contains("Manage Test Cookies");
                    cy.get("button#fides-consent-banner-button-secondary.fides-consent-banner-button.fides-consent-banner-button-secondary")
                      .contains("Reject Test Cookies");
                    cy.get("button#fides-consent-banner-button-primary.fides-consent-banner-button.fides-consent-banner-button-primary")
                      .contains("Accept Test Cookies");

                    // Order matters - it should always be tertiary, then secondary, then primary!
                    cy.get("button").within(buttons => {
                        const buttonIds = buttons.map((_, elem) => elem.id).get();
                        cy.wrap(buttonIds).should("have.ordered.members", [
                            "fides-consent-banner-button-tertiary",
                            "fides-consent-banner-button-secondary",
                            "fides-consent-banner-button-primary",
                        ]);
                    });
                })
            });
        });
    })
});