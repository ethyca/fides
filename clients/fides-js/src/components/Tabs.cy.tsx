import h from "preact";
import Tabs from "./Tabs";

describe("<Tabs />", () => {
  it("renders", () => {
    // see: https://on.cypress.io/mounting-react
    cy.mount(<Tabs />);
  });
});
