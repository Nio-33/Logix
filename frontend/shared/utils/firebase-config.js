// Firebase Web SDK Configuration
// This file contains the Firebase configuration for the frontend

// TODO: Replace these placeholder values with your actual Firebase project configuration
// You can find these values in your Firebase Console > Project Settings > General > Your apps

const firebaseConfig = {
    apiKey: "AIzaSyCFcHF-IwCIas46N0ny1VdzPnjRj4oV-dU",
    authDomain: "logix-a94ec.firebaseapp.com",
    projectId: "logix-a94ec",
    storageBucket: "logix-a94ec.firebasestorage.app",
    messagingSenderId: "162731401337",
    appId: "1:162731401337:web:b0305b6a25ebf75c95b4a8",
    measurementId: "G-FJSFV50QZR"
};

// Export the configuration
if (typeof module !== 'undefined' && module.exports) {
    module.exports = firebaseConfig;
} else {
    window.firebaseConfig = firebaseConfig;
}