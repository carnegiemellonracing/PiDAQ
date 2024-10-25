import { initializeApp, applicationDefault, cert } from "firebase-admin/app";
import {
    getFirestore,
    Timestamp,
    FieldValue,
    Filter,
} from "firebase-admin/firestore";

import serviceAccount from "./serviceAccountKey.json" with {type: "json"}; // Need to add this file

initializeApp({
    credential: cert(serviceAccount),
});

const db = getFirestore();
const testsRef = db.collection("tests");

export async function getTestData() {
    const snapshot = await testsRef.get();
    return snapshot;
}

export async function putTestData(data) {
  const currTestRef = testsRef.doc(data.info.name);
  await currTestRef.set(data)
}
