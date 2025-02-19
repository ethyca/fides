// Nextjs build prerendering of 500 and 404 pages fails
// Issue: https://github.com/vercel/turborepo/issues/9335
// Workaround: https://github.com/vercel/turborepo/issues/9335#issuecomment-2607281729
const fs = require("fs");

const nodeModulesPath = "./node_modules/";
fs.rmSync(nodeModulesPath + "react", { recursive: true, force: true });
fs.rmSync(nodeModulesPath + "react-dom", { recursive: true, force: true });
