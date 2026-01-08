import { Key } from "react";

import { Flex, Button, Text, SparkleIcon, Dropdown, Icons } from "fidesui";
import _ from "lodash";

import { TreeActions, ActionDict, Plural } from "./types";
import { pluralize } from "~/features/common/utils";

export const AsyncTreeFooter = ({
  selectedKeys,
  actions: {
    nodeActions,
    primaryAction
  },
  taxonomy
}: {
  selectedKeys: Key[],
  actions: TreeActions<ActionDict>,
  taxonomy: Plural 
}) => {

  return <>
    <Flex justify="space-between" align="center" gap="small">
      <Button
        aria-label={`${nodeActions[primaryAction]} ${selectedKeys.length} Selected Nodes`}
        icon={<SparkleIcon size={12} />}
        size="small"
        onClick={() =>
          nodeActions[primaryAction]?.callback(
            selectedKeys,
            []
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
          items: nodeActions
            ? Object.entries(nodeActions).map(
              ([key, { label, disabled }]) => ({
                key,
                label,
                // disabled: disabled(
                //   selectedNodeKeys.flatMap((nodeKey) => {
                //     const node = findNodeByUrn(
                //       treeData,
                //       nodeKey.toString(),
                //     );
                //     return node ? [node] : [];
                //   }),
                // ),
              }),
            )
            : [],
          onClick: ({ key, domEvent }) => {
            domEvent.preventDefault();
            domEvent.stopPropagation();
            nodeActions[key]?.callback(
              selectedKeys,
              []
            );
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
    </Flex>
  </>
}
