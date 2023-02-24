import { Config } from "~/types/config";
import minimalJson from "~/config/examples/minimal.json";
import basicJson from "~/config/examples/basic.json";
import fullJson from "~/config/examples/full.json";

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
    const minimalTyped: Config = minimalJson;
    const basicTyped: Config = basicJson;
    const fullTyped: Config = fullJson;

    expect(minimalTyped).toBeDefined();
    expect(basicTyped).toBeDefined();
    expect(fullTyped).toBeDefined();
  });
});
