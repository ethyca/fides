import { DatasetField } from "~/types/api";

import {
  buildFieldReference,
  parseFieldReference,
  transformFieldsToTreeNodes,
  updateTreeNodeChildren,
} from "../utils";

describe("Dataset Reference Utils", () => {
  describe("buildFieldReference", () => {
    it("should build a field reference string", () => {
      const result = buildFieldReference("dataset1", "users", "email");
      expect(result).toBe("dataset1:users:email");
    });

    it("should handle nested field paths", () => {
      const result = buildFieldReference("dataset1", "users", "profile.email");
      expect(result).toBe("dataset1:users:profile.email");
    });
  });

  describe("parseFieldReference", () => {
    it("should parse a field reference string", () => {
      const result = parseFieldReference("dataset1:users:email");
      expect(result).toEqual({
        datasetKey: "dataset1",
        collectionName: "users",
        fieldPath: "email",
      });
    });

    it("should handle nested field paths", () => {
      const result = parseFieldReference("dataset1:users:profile.email");
      expect(result).toEqual({
        datasetKey: "dataset1",
        collectionName: "users",
        fieldPath: "profile.email",
      });
    });
  });

  describe("transformFieldsToTreeNodes", () => {
    const mockFields: DatasetField[] = [
      {
        name: "id",
        description: "User ID",
        data_categories: [],
        fields: [],
      },
      {
        name: "profile",
        description: "User profile",
        data_categories: [],
        fields: [
          {
            name: "email",
            description: "Email address",
            data_categories: [],
            fields: [],
          },
          {
            name: "name",
            description: "Full name",
            data_categories: [],
            fields: [],
          },
        ],
      },
    ];

    it("should transform fields to tree nodes", () => {
      const result = transformFieldsToTreeNodes(
        mockFields,
        "dataset1",
        "users",
      );

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual({
        key: "dataset1:users:id",
        title: "id",
        value: "dataset1:users:id",
        isLeaf: true,
        selectable: true,
        children: undefined,
      });
    });

    it("should handle nested fields", () => {
      const result = transformFieldsToTreeNodes(
        mockFields,
        "dataset1",
        "users",
      );
      const profileNode = result[1];

      expect(profileNode.key).toBe("dataset1:users:profile");
      expect(profileNode.isLeaf).toBe(false);
      expect(profileNode.children).toHaveLength(2);
      expect(profileNode.children![0]).toEqual({
        key: "dataset1:users:profile.email",
        title: "email",
        value: "dataset1:users:profile.email",
        isLeaf: true,
        selectable: true,
        children: undefined,
      });
    });
  });

  describe("updateTreeNodeChildren", () => {
    const mockTreeData = [
      {
        key: "node1",
        title: "Node 1",
        value: "node1",
        isLeaf: false,
        selectable: false,
        children: undefined,
      },
      {
        key: "node2",
        title: "Node 2",
        value: "node2",
        isLeaf: true,
        selectable: true,
        children: undefined,
      },
    ];

    it("should update tree node children", () => {
      const newChildren = [
        {
          key: "child1",
          title: "Child 1",
          value: "child1",
          isLeaf: true,
          selectable: true,
        },
      ];

      const result = updateTreeNodeChildren(mockTreeData, "node1", newChildren);

      expect(result[0].children).toEqual(newChildren);
      expect(result[1]).toEqual(mockTreeData[1]); // Other nodes unchanged
    });

    it("should update nested tree node children", () => {
      const nestedTreeData = [
        {
          key: "parent",
          title: "Parent",
          value: "parent",
          isLeaf: false,
          selectable: false,
          children: [
            {
              key: "child",
              title: "Child",
              value: "child",
              isLeaf: false,
              selectable: false,
              children: undefined,
            },
          ],
        },
      ];

      const newChildren = [
        {
          key: "grandchild",
          title: "Grandchild",
          value: "grandchild",
          isLeaf: true,
          selectable: true,
        },
      ];

      const result = updateTreeNodeChildren(
        nestedTreeData,
        "child",
        newChildren,
      );

      expect(result[0].children![0].children).toEqual(newChildren);
    });
  });
});
