import { Button, Dropdown, Flex, Icons, Text } from "fidesui";

import { AsyncTreeNodeComponentProps } from "./types";

export const AsyncTreeDataTitle = ({ node, actions }: AsyncTreeNodeComponentProps) => {
  const title = typeof node.title === 'function' ? node.title(node) : node.title

  if (!title) {
    return null;
  }

  return (
    /** TODO: migrate group class to semantic dom after upgrading ant */
    <Flex
      gap={4}
      align="center"
      className={`group ml-1 flex grow ${node.disabled ? "opacity-40" : ""}`}
      aria-label={node.disabled ? `${title.toString()} (ignored)` : title.toString()}
    >
      <Text ellipsis={{ tooltip: title }} className="grow select-none">
        {title}
      </Text>
      <Dropdown
        menu={{
          items: actions
            ? Object.entries(actions).map(([key, { disabled, label }]) => ({
              key,
              disabled: disabled([node]),
              label
            }))
            : [],
          onClick: ({ key, domEvent }) => {
            domEvent.preventDefault();
            domEvent.stopPropagation();
            actions[key]?.callback([key], [node]);
          },
        }}
        destroyOnHidden
        className="group mr-1 flex-none group-[.multi-select]/monitor-tree:pointer-events-none group-[.multi-select]/monitor-tree:opacity-0"
      >
        <Button
          aria-label="Show More Resource Actions"
          icon={
            <Icons.OverflowMenuVertical className="opacity-0 group-hover:opacity-100 group-[.ant-dropdown-open]:opacity-100" />
          }
          type="text"
          size="small"
          className="self-end"
        />
      </Dropdown>
    </Flex>
  );
};
