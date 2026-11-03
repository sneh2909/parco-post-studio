/* Site settings: user accounts for the sign-in screen.
   Manage them with:
     node tools/users.mjs add <userId> "<password>" ["Display name"]
     node tools/users.mjs password <userId> "<new password>"
     node tools/users.mjs remove <userId>
     node tools/users.mjs list
   Then commit and push config.js. Passwords are stored only as salted PBKDF2 hashes. */
window.PARCO_CONFIG={
  users:[
    {"id":"sneh","name":"Sneh","role":"admin","salt":"D7N/g8Clah0VGFclDGG+Ew==","hash":"jptfzK9TEr+XZVPA8JfzVmE0S8sdSBBg1UrRavz1cd8="},
    {"id":"parco","name":"PARCO office","role":"staff","salt":"HQgy3FKPX8ES4l00bdW1Qg==","hash":"6x7tghdDHMzmXYnBvusSwfX1dFayWNHIfz3NQPjFdes="}
  ]
};
