import {
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
} from "fidesui";
import { useFormikContext } from "formik";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import {
  selectSuggestions,
  toggleSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import type { FormValues } from "~/features/system/form";

export const DictSuggestionToggle = () => {
  const dispatch = useAppDispatch();

  const form = useFormikContext<FormValues>();

  const vendorId = form.values.vendor_id;

  const { plus: isPlusEnabled, dictionaryService: isDictionaryServiceEnabled } =
    useFeatures();
  const isShowingSuggestions = useAppSelector(selectSuggestions);
  if (!isPlusEnabled || !isDictionaryServiceEnabled) {
    return null;
  }

  return (
    <Menu>
      <MenuButton
        bg={
          isShowingSuggestions === "showing" ? "terracotta" : "neutral.100"
        }
        as={IconButton}
        size="sm"
        aria-label="Options"
        icon={
          <SparkleIcon
            color={isShowingSuggestions === "showing" ? "white" : "neutral.700"}
          />
        }
        width="32px"
        variant="outline"
        _active={{
          background:
            isShowingSuggestions === "showing"
              ? "terracota_tag"
              : "neutral.200",
        }}
        _hover={{
          background:
            isShowingSuggestions === "showing"
              ? "terracota_tag"
              : "neutral.200",
        }}
        disabled={!vendorId}
        data-testid="dict-suggestions-btn"
      />
      <MenuList>
        <MenuItem
          data-testid="toggle-dict-suggestions"
          onClick={() => {
            dispatch(toggleSuggestions());
          }}
        >
          <Text
            color="terracotta"
            fontSize="xs"
            lineHeight={4}
            fontWeight="medium"
          >
            {isShowingSuggestions === "showing" ? "Hide" : "Show"} suggestions
          </Text>
        </MenuItem>
      </MenuList>
    </Menu>
  );
};
