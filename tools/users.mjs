// Manage PARCO Post Studio sign-in accounts stored in config.js.
//   node tools/users.mjs list
//   node tools/users.mjs add <userId> "<password>" ["Display name"]
//   node tools/users.mjs password <userId> "<new password>"
//   node tools/users.mjs remove <userId>
// Then commit and push config.js to publish the change.
import { pbkdf2Sync, randomBytes } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const file = join(dirname(fileURLToPath(import.meta.url)), '..', 'config.js');
const win = {};
new Function('window', readFileSync(file, 'utf8'))(win);
const users = (win.PARCO_CONFIG && win.PARCO_CONFIG.users) || [];
const norm = v => String(v || '').trim().toLowerCase().replace(/[^a-z0-9._-]/g, '');
const hash = pw => { const salt = randomBytes(16); return { salt: salt.toString('base64'), hash: pbkdf2Sync(pw, salt, 150000, 32, 'sha256').toString('base64') }; };
const [cmd, rawId, pw, name] = process.argv.slice(2);
const id = norm(rawId);
const usage = () => { console.error('Usage: node tools/users.mjs list | add <id> "<password>" ["Name"] | password <id> "<password>" | remove <id>'); process.exit(1); };
const strong = p => { if (!p || p.length < 8) { console.error('Use a password of at least 8 characters.'); process.exit(1); } };

if (cmd === 'list') { users.forEach(u => console.log(`${u.id}\t${u.role || 'staff'}\t${u.name || ''}`)); process.exit(0); }
else if (cmd === 'add') { if (!id) usage(); strong(pw); if (users.some(u => u.id === id)) { console.error(`User "${id}" already exists. Use "password" to change it.`); process.exit(1); }
  users.push({ id, name: name || rawId, role: 'staff', ...hash(pw) }); console.log(`Added ${id}.`); }
else if (cmd === 'password') { if (!id) usage(); strong(pw); const u = users.find(x => x.id === id); if (!u) { console.error(`No user "${id}".`); process.exit(1); }
  Object.assign(u, hash(pw)); console.log(`Password changed for ${id}.`); }
else if (cmd === 'remove') { if (!id) usage(); const i = users.findIndex(u => u.id === id); if (i < 0) { console.error(`No user "${id}".`); process.exit(1); } users.splice(i, 1); console.log(`Removed ${id}.`); }
else usage();

const lines = users.map(u => '    ' + JSON.stringify({ id: u.id, name: u.name, role: u.role || 'staff', salt: u.salt, hash: u.hash })).join(',\n');
writeFileSync(file, `/* Site settings: user accounts for the sign-in screen.
   Manage them with:
     node tools/users.mjs add <userId> "<password>" ["Display name"]
     node tools/users.mjs password <userId> "<new password>"
     node tools/users.mjs remove <userId>
     node tools/users.mjs list
   Then commit and push config.js. Passwords are stored only as salted PBKDF2 hashes. */
window.PARCO_CONFIG={
  users:[
${lines}
  ]
};
`);
console.log('Now commit and push config.js to publish it.');
