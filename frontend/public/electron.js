/**
 * Put electron.js outside /src because /src is intended for React code while electron.js is a node process
 * that should not be included in React bundling and should run separately.
 */

import { app, BrowserWindow } from 'electron';
import path from 'path';
import {fileURLToPath} from 'url';
import isDev from 'electron-is-dev';

function createWindow() {
    const win = new BrowserWindow({
        width: 1000,
        height: 700,
        webPreferences: {
            nodeIntegration: true,
        },
    });
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const PRODUCTION_START_URL = `file://${path.join(__dirname, '../build/index.html')}`;
    console.log('*** prod build idx url=', PRODUCTION_START_URL)
    const startUrl = isDev && false
        ? process.env.ELECTRON_START_URL
        : PRODUCTION_START_URL;
    win.loadURL(startUrl);
}

app.whenReady().then(createWindow);
