import { describe, expect, it } from "@jest/globals";

import { ReactDataNode, 
  // recFindNodeParent 
} from "./utils";

// TODO: add tests for the other utils functions

const MOCK_TREE = [...Array(25)].map((_, i) => {
  const node: ReactDataNode<{}> = {
    key: i,
    children: [
      {
        key: `${i}_1`,
      },
    ],
  };
  return node;
});

const MOCK_TREE_2 = [...Array(25)].map((_, i) => {
  const node: ReactDataNode<{}> = {
    key: i,
    children: [
      {
        key: `${i}_1`,
      },
      {
        key: `${i}_2`,
        children: [
          {
            key: `${i}_2_1`,
          },
          {
            key: `${i}_2_2`,
          },
        ],
      },
      {
        key: `${i}_3`,
      },
    ],
  };
  return node;
});

const getNodeByLevel = (
  level: number,
  data: ReactDataNode<{}>,
): ReactDataNode<{}> | null => {
  const children = data.children?.[0];
  return level > 0 && children ? getNodeByLevel(level - 1, children) : null;
};

const buildDeepTreeMock = (depth: number): ReactDataNode<{}> => ({
  key: depth,
  children: depth > 0 ? [buildDeepTreeMock(depth - 1)] : undefined,
});

// describe(recFindNodeParent.name, () => {
//   it("Should find at depth of 1", () => {
//     const result = recFindNodeParent(MOCK_TREE, "21_1");
//     expect(result).toEqual(MOCK_TREE[22]);
//   });
//   it("Should find at depth of 2", () => {
//     const result = recFindNodeParent(MOCK_TREE, "21_2_2");
//     expect(result).toEqual(MOCK_TREE_2[22].children?.[1]);
//   });
//   it("should return null when parent doesn't exist", () => {
//     const result = recFindNodeParent(MOCK_TREE, MOCK_TREE[0].key);
//     expect(result).toBeNull();
//   });
//   it("should return null when node key doesn't exist", () => {
//     const result = recFindNodeParent(MOCK_TREE, "invalid key");
//     expect(result).toBeNull();
//   });
//   it("should return parent of deeply nested node", () => {
//     const DEEP_TREE_MOCK = buildDeepTreeMock(25);
//     const result = recFindNodeParent([DEEP_TREE_MOCK], 2);
//     expect(result).toEqual(getNodeByLevel(23, DEEP_TREE_MOCK));
//   });
// });
