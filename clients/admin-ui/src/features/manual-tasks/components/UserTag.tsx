import { AntTag as Tag, AntTooltip as Tooltip } from "fidesui";
import { useRouter } from "next/router";

import { USER_PROFILE_ROUTE } from "~/features/common/nav/routes";

import { AssignedUser } from "../mocked/types";

interface Props {
  users: AssignedUser[];
}

export const UserTag = ({ users }: Props) => {
  const router = useRouter();

  if (!users || users.length === 0) {
    return <span>-</span>;
  }

  const handleUserClick = (userId: string) => {
    router.push({
      pathname: USER_PROFILE_ROUTE,
      query: { id: userId },
    });
  };

  return (
    <div className="flex flex-wrap gap-1">
      {users.map((user) => (
        <Tooltip key={user.id} title={user.email_address} placement="top">
          <Tag
            color="corinth"
            className="cursor-pointer hover:opacity-80"
            onClick={() => handleUserClick(user.id)}
          >
            {user.first_name} {user.last_name}
          </Tag>
        </Tooltip>
      ))}
    </div>
  );
};
