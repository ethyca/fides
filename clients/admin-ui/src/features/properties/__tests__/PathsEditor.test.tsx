import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { PathsEditor } from "../PathsEditor";

const Harness: React.FC<{ initial?: string[] }> = ({ initial = [] }) => {
  const [paths, setPaths] = useState<string[]>(initial);
  return <PathsEditor value={paths} onChange={setPaths} />;
};

describe("PathsEditor", () => {
  it("adds a new path on Enter", async () => {
    render(<Harness initial={[]} />);
    const input = screen.getByPlaceholderText(/add a path/i);
    await userEvent.type(input, "/privacy{enter}");
    expect(screen.getByText("/privacy")).toBeInTheDocument();
  });

  it("rejects duplicate paths", async () => {
    render(<Harness initial={["/privacy"]} />);
    const input = screen.getByPlaceholderText(/add a path/i);
    await userEvent.type(input, "/privacy{enter}");
    expect(screen.getAllByText("/privacy")).toHaveLength(1);
    expect(screen.getByText(/already added/i)).toBeInTheDocument();
  });

  it("removes a path when its tag is closed", async () => {
    render(<Harness initial={["/privacy", "/dsr"]} />);
    // Test adaptation: this version of fidesui's antd Tag renders the close
    // affordance as a <button aria-label="Remove">, not an <img name="close">.
    const closeButtons = screen.getAllByRole("button", { name: /remove/i });
    await userEvent.click(closeButtons[0]);
    expect(screen.queryByText("/privacy")).not.toBeInTheDocument();
    expect(screen.getByText("/dsr")).toBeInTheDocument();
  });
});
