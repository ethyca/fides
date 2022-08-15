import { render } from "@testing-library/react";

import SystemTable from "~/features/system/SystemTable";
import { mockSystems } from "~/mocks/data";

describe("SystemTable", () => {
  it("renders an empty state", () => {
    const { getByTestId, queryByTestId } = render(<SystemTable systems={[]} />);
    expect(getByTestId("empty-state")).toBeInTheDocument();
    expect(queryByTestId("systems-table")).toBeNull();
  });

  it("renders a table", () => {
    const numSystems = 10;
    const systems = mockSystems(numSystems);
    const { getByTestId, queryByTestId, getAllByTestId } = render(
      <SystemTable systems={systems} />
    );
    expect(queryByTestId("empty-state")).toBeNull();
    expect(getByTestId("systems-table")).toBeInTheDocument();
    expect(getAllByTestId("systems-row")).toHaveLength(numSystems);
  });
});
