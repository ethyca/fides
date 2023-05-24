import Image from "next/image";
import css from "./style.module.scss";

const Header = () => {
  return (
    <header className={css.header}>
      <Image src="/logo.svg" width={204} height={68} alt="Logo" />
    </header>
  );
};

export default Header;
