import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  Icons,
} from "fidesui";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_MULTIPLE_ROUTE,
} from "~/features/common/nav/routes";

const AddSystemsMenu = () => {
  const { dictionaryService: isCompassEnabled } = useFeatures();
  const router = useRouter();
  return (
    <Flex>
      {isCompassEnabled && (
        <Dropdown
          trigger={["click"]}
          menu={{
            items: [
              {
                label: "Create new system",
                key: "add-system",
                onClick: () => router.push(ADD_SYSTEMS_MANUAL_ROUTE),
              },
              {
                label: "Add multiple systems",
                key: "add-multiple-systems",
                onClick: () => router.push(ADD_SYSTEMS_MULTIPLE_ROUTE),
              },
            ],
          }}
        >
          <Button
            type="primary"
            data-testid="add-system-btn"
            icon={<Icons.ChevronDown />}
          >
            Add system
          </Button>
        </Dropdown>
      )}
      {!isCompassEnabled && (
        <Button
          type="primary"
          data-testid="add-system-btn"
          onClick={() => router.push(ADD_SYSTEMS_MANUAL_ROUTE)}
        >
          Add new system
        </Button>
      )}
    </Flex>
  );
};

export default AddSystemsMenu;
