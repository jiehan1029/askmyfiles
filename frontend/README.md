## Local Development
```bash
npm start
```
This will start the react app on browser (localhost:3000) and the native desktop app.

## Build for Production (and Run it)
```bash
rm -rf node_modules build dist
npm install
npm run build
npm run electron-build
```
Above will compile the production bundle and build the desktop app image. After that, you can run the prod app with the following command.
```
open dist/mac-arm64/frontend.app
```