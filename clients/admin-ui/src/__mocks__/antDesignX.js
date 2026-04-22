// Mock for @ant-design/x — avoids ESM-only transitive deps (refractor) in Jest.
// The real components (Bubble, Sender) are not exercised in unit tests.
const React = require("react");

module.exports = {
  Bubble: () => null,
  Sender: () => null,
};
