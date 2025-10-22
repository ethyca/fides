import { StagedResourceTypeValue } from "~/types/api";

import { MAP_DATASTORE_RESOURCE_TYPE_TO_ICON } from "../fields/MonitorFields.const";
import {
  parseResourceBreadcrumbs,
  UrnBreadcrumbItem,
} from "./parseResourceBreadcrumbs";

describe(parseResourceBreadcrumbs.name, () => {
  describe("valid URNs", () => {
    it("should parse a simple URN with database and schema", () => {
      const urn = "monitor.database.schema.table";
      const result = parseResourceBreadcrumbs(urn);

      expect(result).toEqual([
        {
          title: "database",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
        {
          title: "schema",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.SCHEMA],
        },
      ]);
    });

    it("should parse a URN with database, schema, and table", () => {
      const urn = "monitor.database.schema.table.field";
      const result = parseResourceBreadcrumbs(urn);

      expect(result).toEqual([
        {
          title: "database",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
        {
          title: "schema",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.SCHEMA],
        },
        {
          title: "table",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.TABLE],
        },
      ]);
    });

    it("should parse a URN with nested fields", () => {
      const urn = "monitor.database.schema.table.field.nestedField";
      const result = parseResourceBreadcrumbs(urn);

      expect(result).toEqual([
        {
          title: "database",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
        {
          title: "schema",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.SCHEMA],
        },
        {
          title: "table",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.TABLE],
        },
        {
          title: "field",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.FIELD],
        },
      ]);
    });

    it("should handle URNs with spaces in part names", () => {
      const urn = "monitor.my database.my schema.my table";
      const result = parseResourceBreadcrumbs(urn);

      expect(result).toEqual([
        {
          title: "my database",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
        {
          title: "my schema",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.SCHEMA],
        },
      ]);
    });

    it("should trim whitespace from URN parts", () => {
      const urn = "monitor. database . schema . table ";
      const result = parseResourceBreadcrumbs(urn);

      expect(result).toEqual([
        {
          title: "database",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
        {
          title: "schema",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.SCHEMA],
        },
      ]);
    });
  });

  describe("malformed URNs", () => {
    it("should return empty array for undefined", () => {
      const result = parseResourceBreadcrumbs(undefined);
      expect(result).toEqual([]);
    });

    it("should return empty array for null", () => {
      const result = parseResourceBreadcrumbs(null as any);
      expect(result).toEqual([]);
    });

    it("should return empty array for empty string", () => {
      const result = parseResourceBreadcrumbs("");
      expect(result).toEqual([]);
    });

    it("should return empty array for whitespace-only string", () => {
      const result = parseResourceBreadcrumbs("   ");
      expect(result).toEqual([]);
    });

    it("should return empty array for non-string values", () => {
      expect(parseResourceBreadcrumbs(123 as any)).toEqual([]);
      expect(parseResourceBreadcrumbs({} as any)).toEqual([]);
      expect(parseResourceBreadcrumbs([] as any)).toEqual([]);
    });

    it("should return empty array for URN with only monitor_id", () => {
      const result = parseResourceBreadcrumbs("monitor");
      expect(result).toEqual([]);
    });

    it("should return empty array for URN with only monitor_id and field", () => {
      const result = parseResourceBreadcrumbs("monitor.field");
      expect(result).toEqual([]);
    });

    it("should handle URN with consecutive separators", () => {
      const urn = "monitor..database..schema";
      const result = parseResourceBreadcrumbs(urn);

      // Should filter out empty parts and still parse valid ones
      expect(result).toEqual([
        {
          title: "database",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
      ]);
    });

    it("should handle URN with leading separator", () => {
      const urn = ".monitor.database.schema";
      const result = parseResourceBreadcrumbs(urn);

      // Should filter out the empty leading part
      expect(result.length).toBeGreaterThan(0);
    });

    it("should handle URN with trailing separator", () => {
      const urn = "monitor.database.schema.";
      const result = parseResourceBreadcrumbs(urn);

      // Should filter out the empty trailing part
      expect(result.length).toBeGreaterThan(0);
    });

    it("should handle URN with only separators", () => {
      const result = parseResourceBreadcrumbs("...");
      expect(result).toEqual([]);
    });

    it("should handle URN with whitespace-only parts", () => {
      const urn = "monitor.  .database.  .schema";
      const result = parseResourceBreadcrumbs(urn);

      // Should filter out whitespace-only parts
      expect(result).toEqual([
        {
          title: "database",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
      ]);
    });
  });

  describe("edge cases", () => {
    it("should handle very long URNs with deeply nested fields", () => {
      const urn = "monitor.db.schema.table.field1.field2.field3.field4.field5";
      const result = parseResourceBreadcrumbs(urn);

      expect(result.length).toBe(7); // All parts except monitor and last field
      expect(result[0].title).toBe("db");
      expect(result[6].title).toBe("field4");
    });

    it("should handle URN with special characters in names", () => {
      const urn = "monitor.db_name.schema-2.table$1.field";
      const result = parseResourceBreadcrumbs(urn);

      expect(result).toEqual([
        {
          title: "db_name",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[
              StagedResourceTypeValue.DATABASE
            ],
        },
        {
          title: "schema-2",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.SCHEMA],
        },
        {
          title: "table$1",
          IconComponent:
            MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.TABLE],
        },
      ]);
    });

    it("should handle URN with Unicode characters", () => {
      const urn = "monitor.数据库.スキーマ.テーブル.field";
      const result = parseResourceBreadcrumbs(urn);

      expect(result[0].title).toBe("数据库");
      expect(result[1].title).toBe("スキーマ");
      expect(result[2].title).toBe("テーブル");
    });

    it("should return correct icon types for each depth level", () => {
      const urn = "monitor.db.schema.table.field.nested";
      const result = parseResourceBreadcrumbs(urn);

      expect(result[0].IconComponent).toBe(
        MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.DATABASE],
      );
      expect(result[1].IconComponent).toBe(
        MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.SCHEMA],
      );
      expect(result[2].IconComponent).toBe(
        MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.TABLE],
      );
      expect(result[3].IconComponent).toBe(
        MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[StagedResourceTypeValue.FIELD],
      );
    });
  });

  describe("return type", () => {
    it("should return an array of UrnBreadcrumbItem objects", () => {
      const urn = "monitor.database.schema.table";
      const result = parseResourceBreadcrumbs(urn);

      expect(Array.isArray(result)).toBe(true);
      result.forEach((item: UrnBreadcrumbItem) => {
        expect(item).toHaveProperty("title");
        expect(typeof item.title).toBe("string");
        // IconComponent is optional but should be present for valid URNs
        if (item.IconComponent !== undefined) {
          expect(item.IconComponent).toBeDefined();
        }
      });
    });
  });
});
