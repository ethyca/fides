import { createContext, h } from "preact";
import { FC } from "preact/compat";
import {
  Dispatch,
  StateUpdater,
  useContext,
  useMemo,
  useState,
} from "preact/hooks";

interface VendorButtonContextProps {
  vendorCount?: number;
  setVendorCount: Dispatch<StateUpdater<number | undefined>>;
}

export const VendorButtonContext = createContext<
  VendorButtonContextProps | Record<any, never>
>({});

export const VendorButtonProvider: FC = ({ children }) => {
  const [vendorCount, setVendorCount] = useState<number>();

  const value: VendorButtonContextProps = useMemo(
    () => ({
      vendorCount,
      setVendorCount,
    }),
    [vendorCount, setVendorCount],
  );

  return (
    <VendorButtonContext.Provider value={value}>
      {children}
    </VendorButtonContext.Provider>
  );
};

export const useVendorButton = () => {
  const context = useContext(VendorButtonContext);
  if (!context || Object.keys(context).length === 0) {
    throw new Error(
      "useVendorButton must be used within a VendorButtonProvider",
    );
  }
  return context;
};
