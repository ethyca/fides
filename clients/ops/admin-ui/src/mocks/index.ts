if (typeof window !== "undefined") {
  // eslint-disable-next-line global-require
  const { worker } = require("./browser");
  worker.start();
} else {
  // eslint-disable-next-line global-require
  const { server } = require("./server");
  server.listen();
}

export {};
