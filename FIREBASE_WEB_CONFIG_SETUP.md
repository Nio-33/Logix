# Firebase Web SDK Configuration Setup

## The Problem
Your authentication is failing because the Firebase Web SDK configuration in the frontend uses placeholder API keys instead of real ones from your Firebase project.

## The Solution
You need to get the correct Firebase Web SDK configuration from your Firebase Console and update the frontend files.

## Step-by-Step Instructions

### 1. Go to Firebase Console
1. Open [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **logix-a94ec**

### 2. Get Web App Configuration
1. Click on the **gear icon** (⚙️) next to "Project Overview" in the left sidebar
2. Select **"Project settings"**
3. Scroll down to the **"Your apps"** section
4. If you don't see a web app, click **"Add app"** and select the **web icon** (</>)
5. If you already have a web app, click on the **config icon** (⚙️) next to it

### 3. Copy the Configuration
You'll see something like this:
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "logix-a94ec.firebaseapp.com",
  projectId: "logix-a94ec",
  storageBucket: "logix-a94ec.firebasestorage.app",
  messagingSenderId: "103347196983889168741",
  appId: "1:103347196983889168741:web:XXXXXXXXXXXXXXXX"
};
```

### 4. Update Frontend Files
Replace the placeholder values in these files:

#### A. Update `frontend/auth/login.html`
Find this section (around line 151):
```javascript
const firebaseConfig = {
    apiKey: "AIzaSyBKG8RKZ4QX_7Z8YZ3QZ4Z5Z6Z7Z8Z9ZA",  // TODO: Replace with actual API key
    authDomain: "logix-a94ec.firebaseapp.com",
    projectId: "logix-a94ec",
    storageBucket: "logix-a94ec.firebasestorage.app",
    messagingSenderId: "103347196983889168741",
    appId: "1:103347196983889168741:web:abc123def456"  // TODO: Replace with actual app ID
};
```

Replace with your actual values from Firebase Console.

#### B. Update `frontend/auth/signup.html`
Find the same section and replace with your actual values.

#### C. Update `frontend/shared/utils/firebase-config.js`
Replace the placeholder values with your actual Firebase configuration.

### 5. Enable Authentication Methods
1. In Firebase Console, go to **Authentication** > **Sign-in method**
2. Enable **Email/Password** authentication
3. Click **Save**

### 6. Add Authorized Domains
1. In Firebase Console, go to **Authentication** > **Settings** > **Authorized domains**
2. Add your domains:
   - `localhost` (for development)
   - Your production domain (when you deploy)

## Files to Update
- `frontend/auth/login.html` (lines ~151-158)
- `frontend/auth/signup.html` (lines ~151-158) 
- `frontend/shared/utils/firebase-config.js`

## After Updating
1. Save all files
2. Refresh your browser
3. Try the authentication again

## Verification
- Check browser console for "Firebase initialized successfully"
- No more "api-key-not-valid" errors
- Authentication should work properly

## Need Help?
If you're still having issues after following these steps, please share:
1. The actual Firebase configuration values you got from the console
2. Any new error messages from the browser console
