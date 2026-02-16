// Firebase configuration
import { initializeApp } from "firebase/app";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAMFvRfeHDGgSiQWQ07fGYHxiZsSPKfugM",
  authDomain: "medirelease.firebaseapp.com",
  projectId: "medirelease",
  storageBucket: "medirelease.firebasestorage.app",
  messagingSenderId: "301929437645",
  appId: "1:301929437645:web:afe658a7f4b848645b4c84"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export default app;

