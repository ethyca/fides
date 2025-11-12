import classNames from "classnames";
import {
  AntButton as Button,
  AntInput as Input,
  AntInputProps as InputProps,
  AntSpace as Space,
  SearchLineIcon,
} from "fidesui";

import styles from "./SearchInput.module.scss";

export interface SearchInputProps
  extends Omit<InputProps, "onChange" | "variant"> {
  onChange: (value: string) => void;
  withIcon?: boolean;
  onClear?: () => void;
  variant?: "default" | "compact";
}

const SearchInput = ({
  onChange,
  withIcon,
  onClear,
  placeholder,
  variant = "default",
  ...props
}: SearchInputProps) => {
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.value);

  const isCompact = variant === "compact";

  return (
    <Space.Compact
      className={classNames({
        [styles.searchInput]: true,
        [styles.searchInputCompact]: isCompact,
      })}
      data-testid="search-bar"
    >
      <Input
        autoComplete="off"
        onChange={handleSearchChange}
        placeholder={placeholder || "Search..."}
        prefix={withIcon ? <SearchLineIcon boxSize={4} /> : undefined}
        allowClear={isCompact}
        className="w-full"
        {...props}
      />
      {onClear && !isCompact ? <Button onClick={onClear}>Clear</Button> : null}
    </Space.Compact>
  );
};

export default SearchInput;
