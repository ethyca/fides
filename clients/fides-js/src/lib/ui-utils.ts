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
export const searchForElement = (elementId: string): Promise<HTMLElement> => {
  let attempts = 0;
  let interval = 200;
  return new Promise((resolve) => {
    const checkElement = (currentDelay: number) => {
      const intervalId = setTimeout(() => {
        const foundElement = document.getElementById(elementId);
        if (foundElement) {
          clearInterval(intervalId);
          resolve(foundElement);
        } else {
          attempts += 1;
          // if the container is not found after 5 attempts, increase the interval to reduce the polling frequency
          if (attempts >= 5 && interval < 1000) {
            interval += 200;
          }
          checkElement(interval);
        }
      }, currentDelay);
    };
    checkElement(interval);
  });
};
