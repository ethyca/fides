import classNames from "classnames";
import {
  AntInput as Input,
  AntInputProps as InputProps,
  Icons,
  InputRef,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRef } from "react";
import { useHotkeys } from "react-hotkeys-hook";

import styles from "./SearchInput.module.scss";

export const SEARCH_INPUT_HOTKEY = "/";

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
  const inputRef = useRef<InputRef>(null);

  useHotkeys(
    SEARCH_INPUT_HOTKEY,
    () => {
      inputRef.current?.focus();
    },
    // useKey because we use with '?' elsewhere which conflicts with this hotkey
    // reverse keyup and keydown because otherwise a literal "/" will get typed in the search input
    { useKey: true, keyup: true, keydown: false },
    [inputRef.current],
  );

  return (
    <Input
      ref={inputRef}
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
        [styles.searchInput]: !props.width,
        [styles.searchInputCompact]: isCompact && !props.width,
        [styles.searchInputIcon]: withIcon,
      })}
      data-testid="search-bar"
      {...props}
    />
  );
};

export default SearchInput;
