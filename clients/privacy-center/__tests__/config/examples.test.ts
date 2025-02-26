import basicJson from "~/config/examples/basic.json";
import fullJson from "~/config/examples/full.json";
import minimalJson from "~/config/examples/minimal.json";
import v2ConsentJson from "~/config/examples/v2Consent.json";
import { LegacyConfig } from "~/types/config";

describe("The Config type", () => {
  /**
   * If this test is failing, it's because the Config type has been updated in a way that is not
   * backwards-compatible. To fix this, modify the type so that it is more permissive with what it
   * allows, for example by making a property optional. Then you must handle the old/new
   * compatibility at runtime with sensible defaults.
   *
   * DO NOT make this test pass by updating any example JSON files. Those files are real snapshots
   * of configurations the PC should support.
   *
   * Discussion: https://github.com/ethyca/fides/discussions/2392
   */
  it("is backwards-compatible with old JSON files", () => {
    const minimalTyped: LegacyConfig = minimalJson;
    const basicTyped: LegacyConfig = basicJson;
    const fullTyped: LegacyConfig = fullJson;
    const v2ConsentObject: LegacyConfig = v2ConsentJson;

    expect(minimalTyped).toBeDefined();
    expect(basicTyped).toBeDefined();
    expect(fullTyped).toBeDefined();
    expect(v2ConsentObject).toBeDefined();
  });
});
