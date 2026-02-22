import fs from 'fs'
import { spawnSync } from 'child_process'

function parsePortsFromLog(logText) {
  const lines = logText.split(/\r?\n/)
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const line = lines[i]
    const match = line.match(/system started at http:\/\/127\.0\.0\.1:(\d+) and http:\/\/127\.0\.0\.1:(\d+)/)
    if (match) {
      return {
        apiPort: match[1],
        frontendPort: match[2]
      }
    }
  }
  throw new Error('Could not find system started line in scripts/run.log')
}

function main() {
  const logPath = new URL('../../scripts/run.log', import.meta.url)
  if (!fs.existsSync(logPath)) {
    // eslint-disable-next-line no-console
    console.error('scripts/run.log not found. Please start the app with python scripts/run.py --env dev first.')
    process.exit(1)
  }
  const logText = fs.readFileSync(logPath, 'utf8')
  const { apiPort, frontendPort } = parsePortsFromLog(logText)
  // eslint-disable-next-line no-console
  console.log(`Using API_PORT=${apiPort}, FRONTEND_PORT=${frontendPort} from scripts/run.log`)

  const env = {
    ...process.env,
    USE_EXTERNAL_SERVER: '1',
    FRONTEND_BASE: `http://127.0.0.1:${frontendPort}`,
    API_BASE: `http://127.0.0.1:${apiPort}`
  }

  const result = spawnSync(
    'npx',
    ['playwright', 'test', '--grep', 'Admin Authentication Flow'],
    { stdio: 'inherit', env }
  )

  process.exit(result.status ?? 1)
}

main()

