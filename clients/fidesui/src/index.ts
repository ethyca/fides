// Unmodified components exported directly from ChakraUI
export * from "@chakra-ui/icons";
export * from "@chakra-ui/react";
export { getCSSVar } from "@chakra-ui/utils";
export * from "@chakra-ui/utils";

// Unmodified component exported directly from Ant Design
export type { ThemeConfig as AntThemeConfig } from "antd/es";
export type {
  ButtonProps as AntButtonProps,
  InputProps as AntInputProps,
  SelectProps as AntSelectProps,
  SwitchProps as AntSwitchProps,
  GetProps,
} from "antd/lib";
export {
  Alert as AntAlert,
  Button as AntButton,
  Card as AntCard,
  Checkbox as AntCheckbox,
  Col as AntCol,
  Divider as AntDivider,
  Flex as AntFlex,
  Input as AntInput,
  Layout as AntLayout,
  Radio as AntRadio,
  Row as AntRow,
  Space as AntSpace,
  Switch as AntSwitch,
  Tag as AntTag,
  Tooltip as AntTooltip,
  Typography as AntTypography,
} from "antd/lib";

// Higher-order components
export { CustomSelect as AntSelect } from "./hoc";

/**
 * Custom Re-exports
 *
 * Icons whose names conflict with Chakra's included icons must be explicitly listed. This makes
 * typescript happy, but eslint doesn't understand.
 */
/* eslint-disable import/export */
export { AddIcon, LinkIcon, QuestionIcon, WarningIcon } from "./icons";
export * from "./icons";
/* eslint-enable import/export */

/**
 * prefixed icons from Carbon Icons
 * @example <Icons.download size={14} />
 */
export * as Icons from "@carbon/icons-react";
/* end prefixed icons */

export * from "./FidesUIProvider";
export { extendTheme, theme } from "./FidesUITheme";

/**
 * Custom Components
 * These components are custom to FidesUI and are not included in ChakraUI, although they may rely on ChakraUI components.
 */
export { CheckboxTree } from "./components/checkbox-tree";
export { ClassifiedDataCategoryDropdown } from "./components/classified-data-category-dropdown";
export type { ColumnMetadata } from "./components/column-dropdown";
export { ColumnDropdown } from "./components/column-dropdown";
export { ConfirmationModal } from "./components/confirmation-modal";
export { DataCategoryDropdown } from "./components/data-category-dropdown";
export { ExampleComponent } from "./components/example-component";
export { PrimaryLink, SecondaryLink } from "./components/links";
export { SystemsCheckboxTable } from "./components/systems-checkbox-table";
