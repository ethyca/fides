// Mock for @ant-design/x — its transitive dep (refractor) is ESM-only and
// cannot be required by Jest. These components are not exercised in unit tests.
export const Bubble = () => null;
export const Sender = () => null;
