import "./ui/global.scss";

export const metadata = {
  title: "Privacy Center",
  description: "Privacy Center",
};

const Layout = async ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
};
export default Layout;
