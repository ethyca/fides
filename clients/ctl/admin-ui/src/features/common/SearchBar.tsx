import {
  Input,
  InputGroup,
  InputLeftElement,
  InputProps,
} from "@fidesui/react";

import { SearchLineIcon } from "~/features/common/Icon";

interface Props extends Omit<InputProps, "onChange"> {
  search?: string;
  onChange: (value: string) => void;
}
const SearchBar = ({ search, onChange, ...props }: Props) => {
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.value);

  return (
    <InputGroup size="sm" minWidth="308px">
      <InputLeftElement pointerEvents="none">
        <SearchLineIcon color="gray.300" w="17px" h="17px" />
      </InputLeftElement>
      <Input
        autoComplete="off"
        type="search"
        minWidth={200}
        size="sm"
        borderRadius="md"
        value={search}
        name="search"
        onChange={handleSearchChange}
        {...props}
      />
    </InputGroup>
  );
};

export default SearchBar;
