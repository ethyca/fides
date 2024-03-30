# @fidesui/react

Bundles all of the FidesUI components into one package for easier consumption.

## Installation

```bash
yarn add @fidesui/react
```

## Usage

Wrap your app in a `<FidesProvider />` component:

```tsx
import { ThemeProvider as FidesProvider } from "@fidesui/react";

export const App: React.FC = ({ children }) => {
  return <FidesProvider>{children}</FidesProvider>;
};
```

To use a component, import it from the package and use as desired:

```tsx
import { Button as FidesButton } from "@fidesui/react";

export const Button = () => {
  return <FidesButton colorScheme="blue">Hello World</FidesButton>;
};
```

Note: you can import components individually as well if you don't want to include the entire bundle.
