import h from "preact";
import TcfTabs from "./TcfTabs";

describe("<TcfTabs />", () => {
  // eslint-disable-next-line jest/expect-expect
  it("renders", () => {
    cy.mount(<TcfTabs />);
  });
});
