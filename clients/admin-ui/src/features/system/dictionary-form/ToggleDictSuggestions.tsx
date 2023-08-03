import {
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
} from "@fidesui/react";
import { useFormikContext } from "formik";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import {
  resetSuggestions,
  selectSuggestions,
  toggleSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";

export const DictSuggestionToggle = () => {
  const dispatch = useAppDispatch();

  const form = useFormikContext();

  // @ts-ignore
  const vendorId = form.values?.meta?.vendor?.id;
  const { plus: isPlusEnabled, dictionaryService: isDictionaryServiceEnabled } =
    useFeatures();
  const isShowingSuggestions = useAppSelector(selectSuggestions);
  if (!isPlusEnabled || !isDictionaryServiceEnabled) {
    return null;
  }

  return (
    <Menu>
      {/* @ts-ignore */}
      <MenuButton
        bg={
          isShowingSuggestions === "showing" ? "complimentary.500" : "gray.100"
        }
        as={IconButton}
        aria-label="Options"
        icon={
          <SparkleIcon
            color={isShowingSuggestions === "showing" ? "white" : "gray.700"}
          />
        }
        width="32px"
        variant="outline"
        _active={{
          background:
            isShowingSuggestions === "showing"
              ? "complimentary.300"
              : "gray.200",
        }}
        _hover={{
          background:
            isShowingSuggestions === "showing"
              ? "complimentary.300"
              : "gray.200",
        }}
        disabled={!vendorId}
      />
      <MenuList>
        <MenuItem
          onClick={() => {
            dispatch(toggleSuggestions());
          }}
        >
          <Text
            color="complimentary.500"
            fontSize="xs"
            lineHeight={4}
            fontWeight="medium"
          >
            {isShowingSuggestions === "showing" ? "Hide" : "Show"} Suggestions
          </Text>
        </MenuItem>
        <MenuItem
          onClick={() => {
            dispatch(resetSuggestions());
          }}
        >
          <Text fontSize="xs" lineHeight={4} fontWeight="medium">
            Reset Suggestions
          </Text>
        </MenuItem>
      </MenuList>
    </Menu>
  );
};
