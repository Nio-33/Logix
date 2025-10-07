// Firebase Web SDK Configuration
// This file contains the Firebase configuration for the frontend

// TODO: Replace these placeholder values with your actual Firebase project configuration
// You can find these values in your Firebase Console > Project Settings > General > Your apps

const firebaseConfig = {
    // Get this from Firebase Console > Project Settings > General > Web apps
    apiKey: "YOUR_FIREBASE_API_KEY",  // Replace with your actual API key
    authDomain: "logix-a94ec.firebaseapp.com",  // This should be correct
    projectId: "logix-a94ec",  // This should be correct
    storageBucket: "logix-a94ec.firebasestorage.app",  // This should be correct
    messagingSenderId: "103347196983889168741",  // This should be correct
    appId: "YOUR_FIREBASE_APP_ID"  // Replace with your actual app ID
};

// Export the configuration
if (typeof module !== 'undefined' && module.exports) {
    module.exports = firebaseConfig;
} else {
    window.firebaseConfig = firebaseConfig;
}