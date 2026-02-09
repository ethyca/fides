import SearchInput, { SearchInputProps } from "~/features/common/SearchInput";

export const DebouncedSearchInput = ({ ...props }: SearchInputProps) => {
  return <SearchInput debounce {...props} />;
};
