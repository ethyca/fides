import h from "preact";
import Tabs from "./Tabs";

describe("<Tabs />", () => {
  it("renders", () => {
    cy.mount(<Tabs />);
  });
});
