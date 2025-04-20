## Project Directory

The frontend is an Electron application with React and TypeScript. The app is boostrapped using electron-vite with a nested react project (w/ zustand for state management, shadcn-ui + tailwindCSS for UI) as renderer for the separation of concerns. Frontend folder structure is like the follows.

```
frontend/
├── resources/
├── src/
│   ├── main/                  # Electron main process
│   ├── preload/               # Preload script
│   └── renderer/              # UI: React + Tailwind + shadcn-ui
│       ├── src/                    
│       │   ├── store/         # State management (Zustand)
│       │   ├── shared/        # Shared component library (Shadcn-ui)
│       │   ├── main.tsx
│       │   ├── ...           
│       ├── index.html
│       ├── package.json       # UI dependencies
│       ├── ...
├── electron.vite.config.ts    # vite config for all 3 parts (including renderer)
├── electron-builder.yml       # Production build config
├── package.json               # Acts as orchestrator + electron dependencies
├── tsconfig.json              # Root TS config with paths for all 3 parts
├── ...
```

**Environment variables**
`/frontend/.env` file is commited (though usually not recommended) to include necessary env vars that matches the setting when running backend in `make backend-up`.

**Other dev notes**

- Frontend runs on port 5173.
- Use different package.json in root frontend/ and renderer/ but share same vite config file and tsconfig files -- that will make aliases and import resolution much easier.
- Shadcn components are saved into a shared folder under /src, this makes it easier to handle import alias.
- Vite and Typescript configuration files are at the root directory and shared by all.
- Check production build: use this cmd to extract the app.asar to folder /extracted-app `npx asar extract dist/mac-arm64/AskMyFiles.app/Contents/Resources/app.asar extracted-app`.
- Launch the build by running `dist/mac-arm64/AskMyFiles.app/Contents/MacOS/AskMyFiles`


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
