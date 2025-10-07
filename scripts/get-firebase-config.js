#!/usr/bin/env node

/**
 * Firebase Configuration Helper
 * 
 * This script helps you get the correct Firebase Web SDK configuration
 * for your project.
 */

console.log(`
🔥 FIREBASE CONFIGURATION HELPER 🔥

Your authentication is failing because the frontend is using placeholder API keys.

TO FIX THIS:

1. Go to Firebase Console: https://console.firebase.google.com/
2. Select your project: logix-a94ec
3. Click the gear icon (⚙️) → Project settings
4. Scroll down to "Your apps" section
5. If you don't have a web app, click "Add app" and select web (</>)
6. If you have a web app, click the config icon (⚙️) next to it
7. Copy the firebaseConfig object

You'll get something like:
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "logix-a94ec.firebaseapp.com",
  projectId: "logix-a94ec",
  storageBucket: "logix-a94ec.firebasestorage.app",
  messagingSenderId: "103347196983889168741",
  appId: "1:103347196983889168741:web:XXXXXXXXXXXXXXXX"
};

THEN UPDATE THESE FILES:
- frontend/auth/login.html (lines ~151-158)
- frontend/auth/signup.html (lines ~151-158)

ALSO ENABLE AUTHENTICATION:
1. In Firebase Console → Authentication → Sign-in method
2. Enable "Email/Password"
3. Click Save

CURRENT PLACEHOLDER VALUES (INVALID):
- apiKey: "AIzaSyBKG8RKZ4QX_7Z8YZ3QZ4Z5Z6Z7Z8Z9ZA"
- appId: "1:103347196983889168741:web:abc123def456"

These are just placeholders and won't work!
`);

// Check if we can detect the current invalid config
const fs = require('fs');
const path = require('path');

const loginFile = path.join(__dirname, '..', 'frontend', 'auth', 'login.html');

if (fs.existsSync(loginFile)) {
    const content = fs.readFileSync(loginFile, 'utf8');
    if (content.includes('AIzaSyBKG8RKZ4QX_7Z8YZ3QZ4Z5Z6Z7Z8Z9ZA')) {
        console.log('❌ CONFIRMED: Using placeholder API key in login.html');
    }
    if (content.includes('abc123def456')) {
        console.log('❌ CONFIRMED: Using placeholder app ID in login.html');
    }
}

console.log(`
🚀 AFTER UPDATING:
1. Save all files
2. Refresh your browser
3. Check console for "Firebase initialized successfully"
4. No more "api-key-not-valid" errors
5. Authentication should work!

Need help? Check FIREBASE_WEB_CONFIG_SETUP.md for detailed instructions.
`);
