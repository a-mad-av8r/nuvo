#!/usr/bin/env node
'use strict';
// The only command/config implementation is the bundled Rust CLI.
const {spawnSync} = require('node:child_process');
const path = require('node:path');
const os = require('node:os');
const root = path.resolve(__dirname, '..');
const cache = path.join(process.env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache'), 'nuvo', '0.1.0');
const result = spawnSync('cargo', ['run', '--quiet', '--release', '--offline', '--locked', '--manifest-path', path.join(root, 'native', 'nuvo-cli', 'Cargo.toml'), '--target-dir', cache, '--', ...process.argv.slice(2)], {stdio: 'inherit'});
if (result.error) {
  console.error(JSON.stringify({status:'refused', code:'NUVO_TOOLCHAIN_MISSING', message:'Rust and Cargo are required; see https://github.com/a-mad-av8r/nuvo'}));
  process.exit(2);
}
if (result.status === 101 || result.status === null) {
  console.error(JSON.stringify({status:'refused', code:'NUVO_BUILD_FAILED', message:'Could not build the bundled Nuvo CLI with Cargo.'}));
  process.exit(2);
}
process.exit(result.status);
