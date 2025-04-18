// Unmodified components exported directly from ChakraUI
export * from "@chakra-ui/icons";
export * from "@chakra-ui/react";
export { getCSSVar } from "@chakra-ui/react";
export * from "@chakra-ui/utils";

// Unmodified component exported directly from Ant Design
export type { ThemeConfig as AntThemeConfig } from "antd/es";
export type {
  ButtonProps as AntButtonProps,
  CollapseProps as AntCollapseProps,
  FlexProps as AntFlexProps,
  FormInstance as AntFormInstance,
  InputProps as AntInputProps,
  ListProps as AntListProps,
  MenuProps as AntMenuProps,
  RadioGroupProps as AntRadioGroupProps,
  SelectProps as AntSelectProps,
  SwitchProps as AntSwitchProps,
  TabsProps as AntTabsProps,
  TagProps as AntTagProps,
  TooltipProps as AntTooltipProps,
  GetProps,
  InputRef,
  RadioChangeEvent,
} from "antd/lib";
export {
  Alert as AntAlert,
  Avatar as AntAvatar,
  Breadcrumb as AntBreadcrumb,
  Button as AntButton,
  Card as AntCard,
  Checkbox as AntCheckbox,
  Col as AntCol,
  Collapse as AntCollapse,
  Divider as AntDivider,
  Dropdown as AntDropdown,
  Empty as AntEmpty,
  Flex as AntFlex,
  Form as AntForm,
  Input as AntInput,
  Layout as AntLayout,
  List as AntList,
  Menu as AntMenu,
  message as AntMessage,
  Radio as AntRadio,
  Row as AntRow,
  Skeleton as AntSkeleton,
  Space as AntSpace,
  Switch as AntSwitch,
  Tabs as AntTabs,
  Tooltip as AntTooltip,
  Typography as AntTypography,
} from "antd/lib";
export type {
  BreadcrumbItemType as AntBreadcrumbItemType,
  BreadcrumbProps as AntBreadcrumbProps,
} from "antd/lib/breadcrumb/Breadcrumb";
export type { ListItemProps as AntListItemProps } from "antd/lib/list";
export type {
  BaseOptionType as AntBaseOptionType,
  DefaultOptionType as AntDefaultOptionType,
} from "antd/lib/select";

// Higher-order components
export { CustomSelect as AntSelect } from "./hoc";
export { CustomDateRangePicker as AntDateRangePicker } from "./hoc";

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
export type { ColumnMetadata } from "./components/column-dropdown";
export { ColumnDropdown } from "./components/column-dropdown";
export { ConfirmationModal } from "./components/confirmation-modal";
export { DataCategoryDropdown } from "./components/data-category-dropdown";
export { ExampleComponent } from "./components/example-component";
export { FloatingMenu } from "./components/floating-menu";
export { PrimaryLink, SecondaryLink } from "./components/links";
export { SystemsCheckboxTable } from "./components/systems-checkbox-table";
export { CustomTag as AntTag } from "./hoc";
