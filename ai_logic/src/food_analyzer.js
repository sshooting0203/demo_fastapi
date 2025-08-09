// index.js (또는 food_analyzer.js)
import 'dotenv/config'; 
import admin from 'firebase-admin';
import { gemini15Flash, googleAI } from '@genkit-ai/googleai';
import { genkit } from 'genkit';

// configure Genkit instance with Google AI plugin
const ai = genkit({
  plugins: [googleAI({ apiKey: process.env.GOOGLE_API_KEY })], // 환경 변수 읽기
  model: gemini15Flash,
});


const helloFlow = ai.defineFlow('helloFlow', async (name) => {
  const { text } = await ai.generate(`Hello Gemini, my name is ${name}`);
  console.log(text);
});

// helloFlow('Chris');

if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.applicationDefault(),
    // 또는 JSON 직접 로드:
    // credential: admin.credential.cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_JSON))
  });
}

const db = admin.firestore();

async function getUserProfile(uid) {
  try {
    const docRef = db.collection('users').doc(uid);
    const docSnap = await docRef.get();

    if (!docSnap.exists) {
      console.error(`❌ User ${uid} not found`);
      return null;
    }

    console.log(`✅ User ${uid} data:`, docSnap.data());
    return docSnap.data();
  } catch (err) {
    console.error('🔥 Error reading user profile:', err);
    return null;
  }
}

(async () => {
  await getUserProfile('DUMMY_user_01');
})();
