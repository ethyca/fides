import { Button, Dropdown, Flex, Icons, SparkleIcon, Text } from "fidesui";
import { Key } from "react";

import { pluralize } from "~/features/common/utils";

import { ActionDict, Plural, TreeActions } from "./types";

export const AsyncTreeFooter = ({
  selectedKeys,
  actions,
  taxonomy,
}: {
  selectedKeys: Key[];
  actions?: TreeActions<ActionDict>;
  taxonomy: Plural;
}) => {
  return (
    <Flex justify="space-between" align="center" gap="small">
      {actions ? (
        <>
          <Button
            aria-label={`${actions.nodeActions[actions.primaryAction]} ${selectedKeys.length} selected ${pluralize(selectedKeys.length, ...taxonomy)}`}
            /** TODO: add icons to the action definitions to render here * */
            icon={<SparkleIcon size={12} />}
            size="small"
            onClick={() =>
              actions.nodeActions[actions.primaryAction]?.callback(
                selectedKeys,
                [],
                // selectedNodeKeys.flatMap((nodeKey) => {
                //   const node = findNodeByUrn(treeData, nodeKey.toString());
                //   return node ? [node] : [];
                // }),
              )
            }
            className="flex-none"
          />
          <Text
            ellipsis
          >{`${selectedKeys.length} ${pluralize(selectedKeys.length, ...taxonomy)} selected`}</Text>
          <Dropdown
            menu={{
              items: actions.nodeActions
                ? Object.entries(actions.nodeActions).map(
                    ([key, { label, disabled }]) => ({
                      key,
                      label,
                      disabled: disabled?.([]),
                    }),
                  )
                : [],
              onClick: ({ key, domEvent }) => {
                domEvent.preventDefault();
                domEvent.stopPropagation();
                actions.nodeActions[key]?.callback(selectedKeys, []);
              },
            }}
            destroyOnHidden
            className="group mr-1 flex-none"
          >
            <Button
              aria-label={`Show more ${taxonomy[0]} actions`}
              icon={<Icons.OverflowMenuVertical />}
              size="small"
              className="self-end"
            />
          </Dropdown>
        </>
      ) : null}
    </Flex>
  );
};
