import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Text,
} from "@fidesui/react";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  toggleSuggestions,
  selectSuggestions,
  selectDictEntry,
  resetSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import { useFormikContext } from "formik";
import { useFeatures } from "~/features/common/features";

export function DictSuggestionToggle() {
  const dispatch = useAppDispatch();

  const form = useFormikContext();

  const vendorId = form.values?.meta?.vendor?.id;
  const dictEntry = useAppSelector(selectDictEntry(vendorId || ""));
  const { plus: isPlusEnabled, dictionaryService: isDictionaryServiceEnabled } =
    useFeatures();
  const isShowingSuggestions = useAppSelector(selectSuggestions);
  console.log("test", isShowingSuggestions);
  if (!isPlusEnabled || !isDictionaryServiceEnabled) {
    return null;
  }

  return (
    <Menu>
      {/* @ts-ignore*/}
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
            console.log("test");
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
}
