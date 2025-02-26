import { mergeColumns } from "~/features/datamap";

describe("Merge Columns", () => {
  const columns = [
    {
      isVisible: true,
      text: "System Name",
      value: "system.name",
      id: 0,
    },
    {
      isVisible: true,
      text: "Data Use",
      value: "system.privacy_declaration.data_use.name",
      id: 1,
    },
    {
      isVisible: true,
      text: "Data Category",
      value: "unioned_data_categories",
      id: 2,
    },
    {
      isVisible: true,
      text: "Data Subject",
      value: "system.privacy_declaration.data_subjects.name",
      id: 3,
    },
    {
      isVisible: true,
      text: "Description",
      value: "system.description",
      id: 4,
    },
  ];

  const updatedColumns = [
    {
      isVisible: true,
      text: "System Name",
      value: "system.name",
      id: 0,
    },
    {
      isVisible: true,
      text: "Data Use",
      value: "system.privacy_declaration.data_use.name",
      id: 1,
    },

    {
      isVisible: true,
      text: "Data Category",
      value: "unioned_data_categories",
      id: 2,
    },
    {
      isVisible: true,
      text: "Data Subject",
      value: "system.privacy_declaration.data_subjects.name",
      id: 3,
    },
    {
      isVisible: true,
      text: "Description",
      value: "system.description",
      id: 4,
    },
  ];

  it("should return updatedColumns if columns is undefined", () => {
    expect(mergeColumns(undefined, updatedColumns)).toEqual(updatedColumns);
  });

  it("should return columns identical to the cache if nothing changed", () => {
    expect(mergeColumns(columns, updatedColumns)).toEqual(columns);
  });

  it("should remove columns from cache that are no longer in the updated payload", () => {
    const removedOneColumn = [...updatedColumns];
    removedOneColumn.splice(0, 1);
    expect(mergeColumns(columns, removedOneColumn)).toEqual(removedOneColumn);
  });

  it("should shift column to end of list when it's renamed", () => {
    const renamedOneColumn = [...columns];
    renamedOneColumn[0].value = "updated column key";

    const correctResponse = [...updatedColumns];
    correctResponse.push(
      correctResponse.shift() as (typeof correctResponse)[0],
    );
    expect(mergeColumns(renamedOneColumn, updatedColumns)).toEqual(
      correctResponse,
    );
  });
});
