import { Tag } from "fidesui";

interface RoleTagProps {
  role: "producer" | "consumer";
}

const RoleTag = ({ role }: RoleTagProps) => (
  <Tag bordered={false} className="text-xs">
    {role === "producer" ? "Producer" : "Consumer"}
  </Tag>
);

export default RoleTag;
