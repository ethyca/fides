import {
  AntDescriptions as Descriptions,
  AntModal as Modal,
  AntModalProps as ModalProps,
  AntTypography as Typography,
  LIST_HOTKEYS,
} from "fidesui";

import { SEARCH_INPUT_HOTKEY } from "~/features/common/SearchInput";

import { FIELD_ACTION_HOTKEYS } from "./FieldActions.const";
import { BULK_LIST_HOTKEYS } from "./useBulkListSelect";

export const HotkeysHelperModal = ({ ...props }: ModalProps) => {
  return (
    <Modal title="Keyboard shortcuts" footer={null} {...props}>
      <Descriptions
        bordered
        column={1}
        items={[
          {
            key: `${LIST_HOTKEYS.NAVIGATE_UP}-${LIST_HOTKEYS.NAVIGATE_DOWN}`,
            label: (
              <>
                <Typography.Text keyboard>
                  {LIST_HOTKEYS.NAVIGATE_DOWN}
                </Typography.Text>{" "}
                /{" "}
                <Typography.Text keyboard>
                  {LIST_HOTKEYS.NAVIGATE_UP}
                </Typography.Text>
              </>
            ),
            children: "Activate the next/previous field",
          },
          {
            key: BULK_LIST_HOTKEYS.TOGGLE_SELECTION,
            label: (
              <Typography.Text keyboard>
                {BULK_LIST_HOTKEYS.TOGGLE_SELECTION}
              </Typography.Text>
            ),
            children: "Toggle checkbox of the active field",
          },
          {
            key: BULK_LIST_HOTKEYS.SELECT_ALL,
            label: (
              <Typography.Text keyboard>
                {BULK_LIST_HOTKEYS.SELECT_ALL}
              </Typography.Text>
            ),
            children: "Select all fields",
          },
          {
            key: BULK_LIST_HOTKEYS.DESELECT_ALL,
            label: (
              <Typography.Text keyboard>
                {BULK_LIST_HOTKEYS.DESELECT_ALL}
              </Typography.Text>
            ),
            children: "Deselect all fields",
          },
          {
            key: LIST_HOTKEYS.CLEAR_FOCUS,
            label: (
              <Typography.Text keyboard>
                {LIST_HOTKEYS.CLEAR_FOCUS}
              </Typography.Text>
            ),
            children: "Clear the active field",
          },
          {
            key: FIELD_ACTION_HOTKEYS.TOGGLE_DRAWER,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.TOGGLE_DRAWER}
              </Typography.Text>
            ),
            children: "Open/close details drawer for active field",
          },
          {
            key: FIELD_ACTION_HOTKEYS.REVIEW,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.REVIEW}
              </Typography.Text>
            ),
            children: "Mark the active field as reviewed",
          },
          {
            key: FIELD_ACTION_HOTKEYS.PROMOTE,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.PROMOTE}
              </Typography.Text>
            ),
            children: "Approve the active field",
          },
          {
            key: FIELD_ACTION_HOTKEYS.MUTE,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.MUTE}
              </Typography.Text>
            ),
            children: "Ignore the active field",
          },
          {
            key: FIELD_ACTION_HOTKEYS.UN_MUTE,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.UN_MUTE}
              </Typography.Text>
            ),
            children: "Restore the active field",
          },
          {
            key: FIELD_ACTION_HOTKEYS.OPEN_CLASSIFICATION_SELECT,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.OPEN_CLASSIFICATION_SELECT}
              </Typography.Text>
            ),
            children: "Edit data categories for the active field",
          },
          {
            key: FIELD_ACTION_HOTKEYS.REFRESH,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.REFRESH}
              </Typography.Text>
            ),
            children: "Refresh the list",
          },
          {
            key: FIELD_ACTION_HOTKEYS.REFRESH,
            label: (
              <Typography.Text keyboard>
                {FIELD_ACTION_HOTKEYS.REFRESH}
              </Typography.Text>
            ),
            children: "Refresh the list",
          },
          {
            key: SEARCH_INPUT_HOTKEY,
            label: <Typography.Text keyboard>/</Typography.Text>,
            children: "Focus the search input",
          },
          {
            key: "?",
            label: (
              <div className="whitespace-nowrap">
                <Typography.Text keyboard>?</Typography.Text> (
                <Typography.Text keyboard>shift</Typography.Text>+
                <Typography.Text keyboard>/</Typography.Text>)
              </div>
            ),
            children: "Open/close this modal",
          },
        ]}
      />
    </Modal>
  );
};
