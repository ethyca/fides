// Unmodified components exported directly from ChakraUI
import { CustomTypography } from "./hoc/CustomTypography";

export * from "@chakra-ui/icons";
export * from "@chakra-ui/react";
export { getCSSVar } from "@chakra-ui/react";
export * from "@chakra-ui/utils";

// Unmodified component exported directly from Ant Design
export type { LocationSelectProps } from "./components/select/LocationSelect";
export { LocationSelect } from "./components/select/LocationSelect";
export type { ThemeConfig as AntThemeConfig } from "antd/es";
export type {
  FilterValue as AntFilterValue,
  SorterResult as AntSorterResult,
  TablePaginationConfig as AntTablePaginationConfig,
} from "antd/es/table/interface";
export type {
  ButtonProps as AntButtonProps,
  CollapseProps as AntCollapseProps,
  DatePickerProps as AntDatePickerProps,
  DropdownProps as AntDropdownProps,
  FlexProps as AntFlexProps,
  FormInstance as AntFormInstance,
  FormItemProps as AntFormItemProps,
  InputProps as AntInputProps,
  ListProps as AntListProps,
  MenuProps as AntMenuProps,
  ModalProps as AntModalProps,
  RadioGroupProps as AntRadioGroupProps,
  SelectProps as AntSelectProps,
  SwitchProps as AntSwitchProps,
  TableProps as AntTableProps,
  TabsProps as AntTabsProps,
  TooltipProps as AntTooltipProps,
  TreeDataNode as AntTreeDataNode,
  TreeProps as AntTreeProps,
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
  Cascader as AntCascader,
  Checkbox as AntCheckbox,
  Col as AntCol,
  Collapse as AntCollapse,
  DatePicker as AntDatePicker,
  Divider as AntDivider,
  Dropdown as AntDropdown,
  Empty as AntEmpty,
  Flex as AntFlex,
  Form as AntForm,
  Image as AntImage,
  Input as AntInput,
  InputNumber as AntInputNumber,
  Layout as AntLayout,
  List as AntList,
  Menu as AntMenu,
  message as AntMessage,
  Modal as AntModal,
  notification as AntNotification,
  Pagination as AntPagination,
  Popover as AntPopover,
  Progress as AntProgress,
  Radio as AntRadio,
  Result as AntResult,
  Row as AntRow,
  Skeleton as AntSkeleton,
  Space as AntSpace,
  Spin as AntSpin,
  Splitter as AntSplitter,
  Steps as AntSteps,
  Switch as AntSwitch,
  Tabs as AntTabs,
  Tree as AntTree,
  TreeSelect as AntTreeSelect,
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
export type { ICustomMultiSelectProps, ICustomSelectProps } from "./hoc";
export {
  CustomDateRangePicker as AntDateRangePicker,
  CustomSelect as AntSelect,
  CustomTable as AntTable,
  CustomTag as AntTag,
  CustomTooltip as AntTooltip,
  CustomTypography as AntTypography,
} from "./hoc";
export type { CustomColumnsType as AntColumnsType } from "./hoc/CustomTable";
export type { CustomTagProps as AntTagProps } from "./hoc/CustomTag";

// Export utils
export * from "./components/data-display/location.utils";
export { isoCodesToOptions } from "./components/select/LocationSelect";

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
export { AddIcon, LinkIcon, WarningIcon } from "./icons";
export * from "./icons";
export {
  CarryOutOutlined as AntCarryOutlined,
  CheckOutlined as AntCheckOutlined,
  CloseOutlined as AntCloseOutlined,
  DownOutlined as AntDownOutlined,
  PlusOutlined as AntPlusOutlined,
  SyncOutlined as AntSyncOutlined,
} from "@ant-design/icons";
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
export { theme as antTheme } from "antd";

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
