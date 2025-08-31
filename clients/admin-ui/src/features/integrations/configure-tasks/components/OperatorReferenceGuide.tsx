import { AntTypography as Typography } from "fidesui";

const { Text, Title, Link } = Typography;

export const OperatorReferenceGuide = () => (
  <div className="px-2 text-white">
    <Title level={5} className="mb-3" style={{ color: "inherit" }}>
      Operator Reference
    </Title>

    <Text strong className="mb-2 block" style={{ color: "inherit" }}>
      All data types:
    </Text>
    <ul className="ml-2 space-y-1">
      <li>Equals: Exact match</li>
      <li>Not equals: Does not exactly match</li>
      <li>
        Exists: Field can be reached{" "}
        <Link
          href="https://www.ethyca.com/docs/dev-docs/privacy-requests/execution#graph-building"
          target="_blank"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          by the DAG
        </Link>{" "}
        regardless of value
      </li>
      <li>
        Does not exist: Field cannot be reached{" "}
        <Link
          href="https://www.ethyca.com/docs/dev-docs/privacy-requests/execution#graph-building"
          target="_blank"
          style={{ color: "inherit", textDecoration: "underline" }}
        >
          by the DAG
        </Link>
      </li>
    </ul>

    <Text strong className="mb-2 mt-4 block" style={{ color: "inherit" }}>
      Strings/Text:
    </Text>
    <ul className="ml-2 space-y-1">
      <li>Starts with: Text begins with value</li>
      <li>Contains: Text includes value anywhere</li>
    </ul>

    <Text strong className="mb-2 mt-4 block" style={{ color: "inherit" }}>
      Numbers:
    </Text>
    <ul className="ml-2 space-y-1">
      <li>
        Equals / Not equals / Greater than / Greater than or equal / Less than /
        Less than or equal
      </li>
    </ul>

    <Text strong className="mb-2 mt-4 block" style={{ color: "inherit" }}>
      Array/List:
    </Text>
    <ul className="ml-2 space-y-1">
      <li>List contains: Value in list</li>
      <li>Not in list: Value not in list</li>
    </ul>
  </div>
);
