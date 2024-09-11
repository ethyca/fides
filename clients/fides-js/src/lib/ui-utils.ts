export const blockPageScrolling = () => {
  document.body.classList.add("fides-no-scroll");
};
export const unblockPageScrolling = () => {
  document.body.classList.remove("fides-no-scroll");
};
export const stripHtml = (html: string) => {
  const doc = new DOMParser().parseFromString(html, "text/html");
  return doc.body.textContent || "";
};
