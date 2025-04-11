The app is set up using electron-vite. Separate react-only dependencies and components into renderer (separation of concerns).


frontend/
├── src/
│   ├── main/                  # Electron main process
│   ├── preload/               # Preload script
│   └── renderer/              # UI: React + Tailwind + shadcn-ui
│       ├── package.json       # UI dependencies
│       ├──NO vite.config.ts     # Vite config for renderer only
│       ├──NO tsconfig.json      # Local TypeScript config (extends root)
│       └── index.html, main.tsx, etc.
├── electron.vite.config.ts    
├── package.json               # Acts as orchestrator: runs both processes
├── tsconfig.json              # Root TS config with paths for all 3 parts


use different package.json in root frontend/ and renderer/ but share same vite config file and tsconfig files -- that will make aliases and import resolution much easier.

also put the shadcn components into a shared folder under /src, this will make import alias resolution much easier too.



# frontend

An Electron application with React and TypeScript

## Recommended IDE Setup

- [VSCode](https://code.visualstudio.com/) + [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) + [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

## Project Setup

### Install

```bash
$ npm install
```

### Development

```bash
$ npm run dev
```

### Build

```bash
# For windows
$ npm run build:win

# For macOS
$ npm run build:mac

# For Linux
$ npm run build:linux
```
