import { getSSOProviderFormValidationSchema } from "../SSOProviderForm";

const BASE_VALUES = {
  provider: "google",
  name: "My Provider",
};

describe("getSSOProviderFormValidationSchema", () => {
  describe("create mode", () => {
    const schema = getSSOProviderFormValidationSchema(false);

    it("requires client_id", async () => {
      await expect(
        schema.validateAt("client_id", { ...BASE_VALUES, client_id: "" }),
      ).rejects.toThrow("Client ID is a required field");
    });

    it("requires client_secret", async () => {
      await expect(
        schema.validateAt("client_secret", {
          ...BASE_VALUES,
          client_secret: "",
        }),
      ).rejects.toThrow("Client Secret is a required field");
    });

    it("passes when credentials are provided", async () => {
      await expect(
        schema.validate({
          ...BASE_VALUES,
          client_id: "my-client-id",
          client_secret: "my-secret",
        }),
      ).resolves.toBeDefined();
    });
  });

  describe("edit mode", () => {
    const schema = getSSOProviderFormValidationSchema(true);

    it("allows empty client_id", async () => {
      await expect(
        schema.validateAt("client_id", { ...BASE_VALUES, client_id: "" }),
      ).resolves.toBeDefined();
    });

    it("allows empty client_secret", async () => {
      await expect(
        schema.validateAt("client_secret", {
          ...BASE_VALUES,
          client_secret: "",
        }),
      ).resolves.toBeDefined();
    });

    it("allows undefined client_id and client_secret", async () => {
      await expect(schema.validate(BASE_VALUES)).resolves.toBeDefined();
    });

    it("accepts provided credentials (rotation)", async () => {
      await expect(
        schema.validate({
          ...BASE_VALUES,
          client_id: "new-client-id",
          client_secret: "new-secret",
        }),
      ).resolves.toBeDefined();
    });
  });
});
