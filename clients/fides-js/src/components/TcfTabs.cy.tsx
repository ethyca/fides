import h from "preact";
import TcfTabs from "./TcfTabs";

describe("<TcfTabs />", () => {
  it("renders", () => {
    cy.mount(<TcfTabs />);
  });
});
