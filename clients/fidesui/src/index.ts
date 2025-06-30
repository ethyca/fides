// Unmodified components exported directly from ChakraUI
import { CustomTypography } from "./hoc/CustomTypography";

export * from "@chakra-ui/icons";
export * from "@chakra-ui/react";
export { getCSSVar } from "@chakra-ui/react";
export * from "@chakra-ui/utils";

// Unmodified component exported directly from Ant Design
export type { ThemeConfig as AntThemeConfig } from "antd/es";
export type { ColumnsType as AntColumnsType } from "antd/es/table";
export type {
  FilterValue as AntFilterValue,
  SorterResult as AntSorterResult,
  TablePaginationConfig as AntTablePaginationConfig,
} from "antd/es/table/interface";
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
  TableProps as AntTableProps,
  TabsProps as AntTabsProps,
  TagProps as AntTagProps,
  TooltipProps as AntTooltipProps,
  UploadFile as AntUploadFile,
  GetProps,
  InputRef,
  RadioChangeEvent,
  UploadFile,
  UploadProps,
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
  DatePicker as AntDatePicker,
  Divider as AntDivider,
  Dropdown as AntDropdown,
  Empty as AntEmpty,
  Flex as AntFlex,
  Form as AntForm,
  Input as AntInput,
  InputNumber as AntInputNumber,
  Layout as AntLayout,
  List as AntList,
  Menu as AntMenu,
  message as AntMessage,
  Modal as AntModal,
  Pagination as AntPagination,
  Radio as AntRadio,
  Row as AntRow,
  Skeleton as AntSkeleton,
  Space as AntSpace,
  Spin as AntSpin,
  Steps as AntSteps,
  Switch as AntSwitch,
  Tabs as AntTabs,
  Tooltip as AntTooltip,
  Upload as AntUpload,
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
export type { UploadChangeParam as AntUploadChangeParam } from "antd/lib/upload";

// Higher-order components
export {
  CustomDateRangePicker as AntDateRangePicker,
  CustomSelect as AntSelect,
  CustomTable as AntTable,
  CustomTag as AntTag,
  CustomTypography as AntTypography,
} from "./hoc";

// Export the destructured Typography components individually
export const AntText = CustomTypography.Text;
export const AntTitle = CustomTypography.Title;
export const AntParagraph = CustomTypography.Paragraph;
export const AntLink = CustomTypography.Link;

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
 * Ant Design Theme System
 */
export { createDefaultAntTheme, defaultAntTheme } from "./ant-theme";

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
export { SelectInline } from "./components/select-inline";
export { SystemsCheckboxTable } from "./components/systems-checkbox-table";
