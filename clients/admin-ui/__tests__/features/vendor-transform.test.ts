import { transformSystemsToCookies } from "~/features/configure-consent/vendor-transform";
import { Cookies, SystemResponse } from "~/types/api";

const mockCookie = (name: string): Cookies => ({ name, path: "/" });
const mockSystem = ({
  name,
  dataUseCookies,
}: {
  name: string;
  dataUseCookies: Record<string, Cookies[]>;
}) => {
  const declarations = Object.entries(dataUseCookies).map(([use, cookies]) => ({
    data_use: use,
    cookies,
  }));
  const system = {
    name,
    fides_key: name,
    privacy_declarations: declarations,
  } as SystemResponse;
  return system;
};

describe("vendor transforms", () => {
  describe("transformSystemsToCookies", () => {
    it("should transform when there are no cookies", () => {
      const systems = [
        mockSystem({ name: "one", dataUseCookies: {} }),
        mockSystem({ name: "two", dataUseCookies: { declaration: [] } }),
      ];
      expect(transformSystemsToCookies(systems)).toEqual([
        { name: "one", id: "one" },
        { name: "two", id: "two" },
      ]);
    });

    it("should transform when there is one cookie", () => {
      const cookie = mockCookie("_ga");
      const systems = [
        mockSystem({ name: "one", dataUseCookies: {} }),
        mockSystem({ name: "two", dataUseCookies: { declaration: [cookie] } }),
      ];
      expect(transformSystemsToCookies(systems)).toEqual([
        { name: "one", id: "one" },
        { name: "two", id: "two", dataUse: "declaration", cookie },
      ]);
    });

    it("should transform when there are multiple cookies on a data use", () => {
      const cookie = mockCookie("_ga");
      const cookie2 = mockCookie("_ga2");
      const systems = [
        mockSystem({ name: "one", dataUseCookies: {} }),
        mockSystem({
          name: "two",
          dataUseCookies: { declaration: [cookie, cookie2] },
        }),
      ];
      expect(transformSystemsToCookies(systems)).toEqual([
        { name: "one", id: "one" },
        { name: "two", id: "two", dataUse: "declaration", cookie },
        { name: "two", id: "two", dataUse: "declaration", cookie: cookie2 },
      ]);
    });

    it("should transform when there are multiple data uses that use the same cookie", () => {
      const cookie = mockCookie("_ga");
      const systems = [
        mockSystem({ name: "one", dataUseCookies: {} }),
        mockSystem({
          name: "two",
          dataUseCookies: { declaration: [cookie], declaration2: [cookie] },
        }),
      ];
      expect(transformSystemsToCookies(systems)).toEqual([
        { name: "one", id: "one" },
        { name: "two", id: "two", dataUse: "declaration", cookie },
        { name: "two", id: "two", dataUse: "declaration2", cookie },
      ]);
    });

    it("should transform multiple systems", () => {
      const cookie = mockCookie("_ga");
      const cookie2 = mockCookie("_ga2");
      const systems = [
        mockSystem({ name: "one", dataUseCookies: { declaration: [cookie] } }),
        mockSystem({
          name: "two",
          dataUseCookies: { declaration: [cookie], declaration2: [cookie2] },
        }),
      ];
      expect(transformSystemsToCookies(systems)).toEqual([
        { name: "one", id: "one", dataUse: "declaration", cookie },
        { name: "two", id: "two", dataUse: "declaration", cookie },
        { name: "two", id: "two", dataUse: "declaration2", cookie: cookie2 },
      ]);
    });
  });
});
