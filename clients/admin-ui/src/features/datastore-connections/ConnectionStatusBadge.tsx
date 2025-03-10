import { AntTag as Tag } from "fidesui";

interface ConnectionBadgeProps {
  disabled: boolean;
}

const ConnectionStatusBadge = ({ disabled }: ConnectionBadgeProps) => {
  return (
    <Tag color={disabled ? "marble" : "success"} className="mr-1 text-center">
      {disabled ? "DISABLED" : "ACTIVE"}
    </Tag>
  );
};

export default ConnectionStatusBadge;
