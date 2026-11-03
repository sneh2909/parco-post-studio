/* Site settings: user accounts for the sign-in screen.
   Manage them with:
     node tools/users.mjs add <userId> "<password>" ["Display name"]
     node tools/users.mjs password <userId> "<new password>"
     node tools/users.mjs remove <userId>
     node tools/users.mjs list
   Then commit and push config.js. Passwords are stored only as salted PBKDF2 hashes. */
window.PARCO_CONFIG={
  users:[
    {"id":"team","name":"PARCO","role":"staff","salt":"wnMGBj40Tq+Og6Th29XneA==","hash":"wWTUR6ktzxyInVh/Q3RpjjLK+ppO2F77o+7IWxLHC/s="}
  ]
};
