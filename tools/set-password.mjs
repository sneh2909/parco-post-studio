// Change the team password shown on the sign-in screen.
// Usage:  node tools/set-password.mjs "new password"
//         node tools/set-password.mjs --off      (removes the password screen)
import { pbkdf2Sync, randomBytes } from 'node:crypto';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const arg = process.argv[2];
if (!arg) { console.error('Usage: node tools/set-password.mjs "new password"   (or --off)'); process.exit(1); }
const file = join(dirname(fileURLToPath(import.meta.url)), '..', 'config.js');
let pw = 'null';
if (arg !== '--off') {
  if (arg.length < 8) { console.error('Use at least 8 characters.'); process.exit(1); }
  const salt = randomBytes(16);
  const hash = pbkdf2Sync(arg, salt, 150000, 32, 'sha256');
  pw = `{salt:${JSON.stringify(salt.toString('base64'))},hash:${JSON.stringify(hash.toString('base64'))},iterations:150000}`;
}
writeFileSync(file, `/* Site settings. Change the team password with:  node tools/set-password.mjs "new password"
   Remove the password screen entirely by setting password to null. */
window.PARCO_CONFIG={
  password:${pw}
};
`);
console.log(arg === '--off' ? 'Password screen removed.' : 'Password updated.', 'Commit and push config.js to publish it.');
