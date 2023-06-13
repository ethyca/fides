import { fillInDefaults } from "~/features/datastore-connections/add-connection/forms/helpers";

describe("connector form helpers", () => {
  describe("fill in defaults", () => {
    const baseDefaultValues = {
      description: "",
      name: "",
      instance_key: "",
    };

    const baseSchema = {
      title: "name",
      type: "string",
    };

    const baseResponse = {
      additionalProperties: false,
      description: "Schema to...",
      properties: {},
      required: ["name"],
      title: "BaseSchema",
      type: "object",
    };

    it("can fill in string defaults", () => {
      const properties = {
        name: baseSchema,
        description: {
          ...baseSchema,
          title: "description",
          default: "default",
        },
        instance_key: { ...baseSchema, title: "instance_key" },
        an_optional_secret: { type: "string", title: "an_optional_secret" },
      };
      const schema = { ...baseResponse, properties };
      expect(fillInDefaults(baseDefaultValues, schema)).toEqual({
        description: "default",
        name: "",
        instance_key: "",
        an_optional_secret: null,
      });
    });

    it("can fill in int defaults", () => {
      const properties = {
        name: baseSchema,
        description: {
          ...baseSchema,
          title: "description",
          default: "default",
        },
        an_optional_secret: { type: "integer", title: "an_optional_secret" },
        instance_key: { ...baseSchema, title: "instance_key" },
        port: { title: "port", default: "8080", type: "integer" },
      };
      const defaultValues = { ...baseDefaultValues, port: "" };
      const schema = { ...baseResponse, properties };
      expect(fillInDefaults(defaultValues, schema)).toEqual({
        description: "default",
        name: "",
        instance_key: "",
        an_optional_secret: 0,
        port: 8080,
      });
    });
  });
});
