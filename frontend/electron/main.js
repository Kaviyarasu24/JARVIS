const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')

const isDev = !app.isPackaged
const BACKEND_PORT = 8765
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`

let mainWindow = null
let pythonProcess = null

// ── Spawn Python FastAPI backend ─────────────────────────────────────────────
function startBackend() {
  const serverPath = path.join(__dirname, '..', '..', 'backend', 'server.py')

  // Try the local venv first, then fall back to system python
  const venvPython = path.join(__dirname, '..', '..', '..', '.jarvis', 'Scripts', 'python.exe')
  const fs = require('fs')
  const pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python'

  console.log(`[Electron] Starting backend: ${pythonCmd} ${serverPath}`)

  pythonProcess = spawn(pythonCmd, [serverPath], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  })

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`)
  })

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`)
  })

  pythonProcess.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`)
  })
}

// ── Wait for backend health check ────────────────────────────────────────────
function waitForBackend(retries = 30) {
  return new Promise((resolve, reject) => {
    let attempts = 0
    const check = () => {
      attempts++
      const req = http.get(`${BACKEND_URL}/api/health`, (res) => {
        if (res.statusCode === 200) {
          console.log('[Electron] Backend is ready')
          resolve()
        } else {
          retry()
        }
      })
      req.on('error', retry)
      req.setTimeout(1000, retry)
    }
    const retry = () => {
      if (attempts >= retries) {
        reject(new Error('Backend failed to start'))
      } else {
        setTimeout(check, 500)
      }
    }
    check()
  })
}

// ── Create main window ───────────────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    frame: false,
    transparent: false,
    backgroundColor: '#0a0412',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hidden',
    show: false,
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    // mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ── IPC handlers for window controls ─────────────────────────────────────────
ipcMain.on('window:minimize', () => mainWindow?.minimize())
ipcMain.on('window:maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize()
  } else {
    mainWindow?.maximize()
  }
})
ipcMain.on('window:close', () => mainWindow?.close())

// ── App lifecycle ────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  startBackend()
  try {
    await waitForBackend()
  } catch (err) {
    console.error('[Electron] Could not start backend:', err.message)
  }
  createWindow()
})

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
  app.quit()
})

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
})
