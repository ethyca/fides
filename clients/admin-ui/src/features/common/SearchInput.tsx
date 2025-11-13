import classNames from "classnames";
import { AntInput as Input, AntInputProps as InputProps, Icons } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import styles from "./SearchInput.module.scss";

export interface SearchInputProps
  extends Omit<InputProps, "onChange" | "variant"> {
  onChange: (value: string) => void;
  withIcon?: boolean;
  variant?: "default" | "compact";
}

const SearchInput = ({
  onChange,
  withIcon = true,
  placeholder,
  variant = "default",
  ...props
}: SearchInputProps) => {
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.value);

  const isCompact = variant === "compact";

  return (
    <Input
      autoComplete="off"
      onChange={handleSearchChange}
      placeholder={placeholder || "Search"}
      aria-label="Search"
      prefix={
        withIcon ? (
          <Icons.Search color={palette.FIDESUI_NEUTRAL_200} />
        ) : undefined
      }
      allowClear
      className={classNames({
        [styles.searchInput]: true,
        [styles.searchInputCompact]: isCompact,
        [styles.searchInputIcon]: withIcon,
      })}
      data-testid="search-bar"
      {...props}
    />
  );
};

export default SearchInput;
