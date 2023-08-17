import { createStacks, Stack } from "../../../src/lib/tcf/stacks";

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
    }
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
    }
  );
});
