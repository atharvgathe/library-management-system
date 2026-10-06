// Node script: builds frontend (watch mode) and launches the Flask server together.
const { spawn } = require('child_process');
const py = process.platform === 'win32' ? 'python' : 'python3';
const run = (cmd, args) => spawn(cmd, args, { stdio: 'inherit', shell: process.platform === 'win32' });
const a = run('node', ['build.js', '--watch']);
const b = run(py, ['app.py']);
process.on('SIGINT', () => { a.kill(); b.kill(); process.exit(); });
