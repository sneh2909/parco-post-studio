/* Site settings: user accounts for the sign-in screen.
   users:[] means no sign-in screen; everyone goes straight to the studio.
   Manage them with:
     node tools/users.mjs add <userId> "<password>" ["Display name"]
     node tools/users.mjs password <userId> "<new password>"
     node tools/users.mjs remove <userId>
     node tools/users.mjs list
   Then commit and push config.js. Passwords are stored only as salted PBKDF2 hashes. */
window.PARCO_CONFIG={
  users:[]
};
