import {
  createStacks,
  getIdsNotRepresentedInStacks,
  Stack,
} from "../../../src/lib/tcf/stacks";

const mockStack = ({
  id,
  purposes,
  specialFeatures,
}: {
  id: number;
  purposes: number[];
  specialFeatures: number[];
}) => {
  const stack: Stack = {
    id,
    name: "stack",
    description: "description",
    purposes,
    specialFeatures,
  };
  return stack;
};

describe("createStacks", () => {
  it.each([
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [] }),
      },
      purposeIds: [2, 7],
      specialFeatureIds: [],
      expected: [1],
    },
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [] }),
      },
      purposeIds: [2, 7, 8],
      specialFeatureIds: [],
      expected: [1],
    },
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [1] }),
      },
      purposeIds: [2, 7, 8],
      specialFeatureIds: [1, 2],
      expected: [1],
    },
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [1] }),
        2: mockStack({ id: 1, purposes: [3, 7], specialFeatures: [1] }),
      },
      purposeIds: [2, 7, 8],
      specialFeatureIds: [1, 2],
      expected: [1],
    },
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [1] }),
        2: mockStack({ id: 2, purposes: [3, 8], specialFeatures: [2] }),
      },
      purposeIds: [2, 3, 7, 8],
      specialFeatureIds: [1, 2],
      expected: [1, 2],
    },
  ])(
    "should return stacks when all match",
    ({ stacks, purposeIds, specialFeatureIds, expected }) => {
      const result = createStacks({
        purposeIds,
        specialFeatureIds,
        stacks: stacks as Record<string, Stack>,
      });

      expect(result.map((r) => r.id)).toEqual(expected);
    },
  );

  it.each([
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [] }),
      },
      purposeIds: [3, 7],
      specialFeatureIds: [],
      expected: [],
    },
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [] }),
      },
      purposeIds: [2],
      specialFeatureIds: [],
      expected: [],
    },
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [1, 3] }),
      },
      purposeIds: [2, 7],
      specialFeatureIds: [1],
      expected: [],
    },
  ])(
    "should not return stacks that do not match",
    ({ stacks, purposeIds, specialFeatureIds, expected }) => {
      const result = createStacks({
        purposeIds,
        specialFeatureIds,
        stacks: stacks as Record<string, Stack>,
      });

      expect(result.map((r) => r.id)).toEqual(expected);
    },
  );

  it.each([
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 7], specialFeatures: [] }),
        2: mockStack({ id: 2, purposes: [2, 7, 9], specialFeatures: [] }),
        3: mockStack({ id: 3, purposes: [2, 4, 7, 9], specialFeatures: [] }),
        4: mockStack({ id: 4, purposes: [3, 5], specialFeatures: [] }),
      },
      purposeIds: [2, 3, 4, 5, 7, 9, 10],
      specialFeatureIds: [],
      expected: [3, 4],
    },
    {
      stacks: {
        1: mockStack({ id: 1, purposes: [2, 4, 7, 9], specialFeatures: [] }),
        2: mockStack({ id: 2, purposes: [2, 7, 9], specialFeatures: [] }),
        3: mockStack({ id: 3, purposes: [2, 4], specialFeatures: [] }),
        4: mockStack({ id: 4, purposes: [3, 5], specialFeatures: [] }),
      },
      purposeIds: [2, 3, 4, 5, 7, 9, 10],
      specialFeatureIds: [],
      expected: [1, 4],
    },
    {
      stacks: {
        1: mockStack({
          id: 1,
          purposes: [],
          specialFeatures: [1, 2],
        }),
        2: mockStack({ id: 2, purposes: [], specialFeatures: [1] }),
        3: mockStack({ id: 3, purposes: [], specialFeatures: [1] }),
        4: mockStack({ id: 4, purposes: [], specialFeatures: [5] }),
      },
      purposeIds: [],
      specialFeatureIds: [1, 2, 5],
      expected: [1, 4],
    },
    {
      stacks: {
        1: mockStack({
          id: 1,
          purposes: [2, 4, 7, 9],
          specialFeatures: [1, 2],
        }),
        2: mockStack({ id: 2, purposes: [2, 7, 9], specialFeatures: [1] }),
        3: mockStack({ id: 3, purposes: [2, 4], specialFeatures: [1] }),
        4: mockStack({ id: 4, purposes: [3, 5], specialFeatures: [] }),
      },
      purposeIds: [2, 3, 4, 5, 7, 9, 10],
      specialFeatureIds: [1, 2],
      expected: [1, 4],
    },
  ])(
    "should return the stack that has the most matches",
    ({ stacks, purposeIds, specialFeatureIds, expected }) => {
      const result = createStacks({ purposeIds, specialFeatureIds, stacks });
      expect(result.map((r) => r.id)).toEqual(expected);
    },
  );
});

describe("getIdsNotRepresentedInStacks", () => {
  it.each([
    {
      stacks: [mockStack({ id: 1, purposes: [1, 2], specialFeatures: [1, 2] })],
      ids: [1, 2, 3],
      modelType: "purposes",
      expected: [3],
    },
    {
      stacks: [
        mockStack({ id: 1, purposes: [1, 2, 3], specialFeatures: [1, 2] }),
      ],
      ids: [1, 2, 3],
      modelType: "purposes",
      expected: [],
    },
    {
      stacks: [
        mockStack({ id: 1, purposes: [1, 2, 3], specialFeatures: [1, 2] }),
      ],
      ids: [1, 2, 3, 4, 5],
      modelType: "purposes",
      expected: [4, 5],
    },
    {
      stacks: [
        mockStack({ id: 1, purposes: [1, 2, 3], specialFeatures: [1, 2] }),
      ],
      ids: [1, 2, 3, 4, 5],
      modelType: "specialFeatures",
      expected: [3, 4, 5],
    },
  ])(
    "can get ids not represented in stacks",
    ({ stacks, ids, modelType, expected }) => {
      const result = getIdsNotRepresentedInStacks({
        ids,
        stacks,
        modelType: modelType as "purposes" | "specialFeatures",
      });
      expect(result).toEqual(expected);
    },
  );
});
