import { CookieKeyConsent, getConsentCookie } from "~/lib/cookie";

describe("getConsentCookie", () => {
    describe("when running outside of a browser", () => {
        it("returns the provided defaults", () => {
            expect(getConsentCookie({})).toEqual({});

            const defaults: CookieKeyConsent = {
                "data_sales": true,
            };
            expect(getConsentCookie(defaults)).toEqual({
                "data_sales": true,
            });
        });
    });

    /**
     * 
     * NOTE: I tried (and failed!) to quickly mock out:
     * - typescript-cookie
     * - "document" global
     * - "window" global
     * - etc.
     * 
     * This is pretty non-obvious for how to do, especially since
     * typescript-cookie is distributed as an ESM module, so we've had to fake
     * it out as "js-cookie" in the moduleNameMapper (see jest.config.js)
     * 
     * ...sorry, maybe another time we can figure this out!
     */
    // describe("when running inside of a browser", () => {
    // });
});
