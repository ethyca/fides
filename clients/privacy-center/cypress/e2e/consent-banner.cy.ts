import { CONSENT_COOKIE_NAME, ConsentBannerOptions, CookieKeyConsent } from "fides-js";

// The fides-consent-demo.html page is wired up to inject the
// `fidesConsentBannerOptions` into the Fides.banner(...) function
declare global {
    interface Window {
        fidesConsentBannerOptions?: ConsentBannerOptions;
    }
}

// We define a custom Cypress command
declare global {
    namespace Cypress {
        interface Chainable {
            visitConsentDemo(bannerOptions?: ConsentBannerOptions): Chainable<any>;
        }
    }
}


describe("Consent banner", () => {
    // Default options to use for all tests
    const testBannerOptions: ConsentBannerOptions = {
        debug: true, // enable debug logging
        labels: {
            bannerDescription: "This test website is overriding the banner description label.",
            primaryButton: "Accept Test",
            secondaryButton: "Reject Test",
            tertiaryButton: "Customize Test",
        }
    };

    const testCookieValue: CookieKeyConsent = {
        data_sales: true,
        tracking: false,
    }

    Cypress.Commands.add("visitConsentDemo", (bannerOptions?: ConsentBannerOptions) => {
        cy.visit("/fides-consent-demo.html", {
            onBeforeLoad: (win) => {
                // eslint-disable-next-line no-param-reassign
                win.fidesConsentBannerOptions = {
                    ...testBannerOptions,
                    ...bannerOptions,
                }
            },
        });
    })

    describe("when disabled", () => {
        beforeEach(() => {
            cy.visitConsentDemo({ isDisabled: true });
        });

        it("does not render", () => {
            cy.get("div#fides-consent-banner").should("not.exist");
            cy.contains("button", "Accept Test").should("not.exist");
        });
    })

    describe("when user has a saved consent cookie", () => {
        beforeEach(() => {
            cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(testCookieValue));
        });

        describe("when banner is not disabled", () => {
            beforeEach(() => {
                cy.visitConsentDemo({ isDisabled: false })
            });

            it("does not render", () => {
                cy.get("div#fides-consent-banner").should("not.exist");
                cy.contains("button", "Accept Test").should("not.exist");
            });
        });
    });

    describe("when user has no saved consent cookie", () => {
        beforeEach(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        });

        describe("when banner is not disabled", () => {
            beforeEach(() => {
                cy.visitConsentDemo({
                    isDisabled: false,
                    isGeolocationEnabled: false,
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
                cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
                    cy.get("div#fides-consent-banner-description.fides-consent-banner-description")
                        .contains("This test website is overriding the banner description label.");
                    cy.get("div#fides-consent-banner-buttons.fides-consent-banner-buttons").within(() => {
                        cy.get("button#fides-consent-banner-button-tertiary.fides-consent-banner-button.fides-consent-banner-button-tertiary")
                            .contains("Customize Test");
                        cy.get("button#fides-consent-banner-button-secondary.fides-consent-banner-button.fides-consent-banner-button-secondary")
                            .contains("Reject Test");
                        cy.get("button#fides-consent-banner-button-primary.fides-consent-banner-button.fides-consent-banner-button-primary")
                            .contains("Accept Test");

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

            it("should allow accepting all", () => {
                cy.contains("button", "Accept Test").should("be.visible").click();
                // TODO: consent.cy.ts uses cy.waitUntil to wait longer for the cookie to save in CI - will this be needed?
                cy.getCookie(CONSENT_COOKIE_NAME).should("exist").then((cookie) => {
                    const cookieKeyConsent = JSON.parse(
                        decodeURIComponent(cookie!.value)
                    );
                    expect(cookieKeyConsent).property("data_sales").is.eql(true);
                    expect(cookieKeyConsent).property("tracking").is.eql(true);
                })
                cy.contains("button", "Accept Test").should("not.be.visible");
            });

            it("should support rejecting all consent options", () => {
                cy.contains("button", "Reject Test").should("be.visible").click();
                // TODO: consent.cy.ts uses cy.waitUntil to wait longer for the cookie to save in CI - will this be needed?
                cy.getCookie(CONSENT_COOKIE_NAME).should("exist").then((cookie) => {
                    const cookieKeyConsent = JSON.parse(
                        decodeURIComponent(cookie!.value)
                    );
                    expect(cookieKeyConsent).property("data_sales").is.eql(false);
                    expect(cookieKeyConsent).property("tracking").is.eql(false);
                })
            });

            it("should navigate to Privacy Center to manage consent options", () => {
                cy.contains("button", "Customize Test").should("be.visible").click();
                cy.url().should("equal", "http://localhost:3000/");
            });

            it.skip("should save the consent request to the Fides API", () => {
                // TODO: add tests for saving to API (ie PATCH /api/v1/consent-request/{id}/preferences...)
                expect(false).is.eql(true);
            });

            it.skip("should support option to display at top or bottom of page", () => {
                // TODO: add tests for top/bottom
                expect(false).is.eql(true);
            });

            it.skip("should support styling with CSS variables", () => {
                // TODO: add tests for CSS
                expect(false).is.eql(true);
            });
        });

        describe("when banner geolocation is enabled", () => {
            it("should show the banner when geolocation country is in EU", () => {
                const locationData = {
                    country: "FR",
                    region: "IDF",
                    location: "FR-IDF",
                }
                cy.intercept("GET", "https://example-api.com/location", { body: locationData });
                cy.visitConsentDemo({
                    geolocationApiUrl: "https://example-api.com/location",
                    isDisabled: false,
                    isGeolocationEnabled: true,
                });
                cy.get("div#fides-consent-banner").should("exist");
                cy.contains("button", "Accept Test").should("exist");
            });

            it("should hide the banner when geolocation country is not in EU", () => {
                const locationData = {
                    country: "US",
                    region: "NY",
                    location: "US-NY",
                }
                cy.intercept("GET", "https://example-api.com/location", { body: locationData });
                cy.visitConsentDemo({
                    geolocationApiUrl: "https://example-api.com/location",
                    isDisabled: false,
                    isGeolocationEnabled: true,
                });
                cy.get("div#fides-consent-banner").should("not.exist");
                cy.contains("button", "Accept Test").should("not.exist");
            });

            it("should show the banner when geolocation country is included in custom isEnabledCountries", () => {
                const locationData = {
                    country: "US",
                    region: "NY",
                    location: "US-NY",
                }
                cy.intercept("GET", "https://example-api.com/location", { body: locationData });
                cy.visitConsentDemo({
                    geolocationApiUrl: "https://example-api.com/location",
                    isDisabled: false,
                    isGeolocationEnabled: true,
                    isEnabledCountries: ["US", "CA"],
                });
                cy.get("div#fides-consent-banner").should("exist");
                cy.contains("button", "Accept Test").should("exist");
            });
        });
    });
});