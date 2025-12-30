/*
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

import { initializeApp, FirebaseApp } from "firebase/app";
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  User,
  onAuthStateChanged,
  Auth,
} from "firebase/auth";

export class AuthService {
  #app: FirebaseApp | undefined;
  #auth: Auth | undefined;

  constructor(config?: Record<string, string>) {
    if (config) {
      this.#app = initializeApp(config);
      this.#auth = getAuth(this.#app);
    }
  }

  get isConfigured() {
    return !!this.#auth;
  }

  signIn() {
    if (!this.#auth) return Promise.reject("Auth not configured");
    const provider = new GoogleAuthProvider();
    return signInWithPopup(this.#auth, provider);
  }

  signOut() {
    if (!this.#auth) return Promise.resolve();
    return firebaseSignOut(this.#auth);
  }

  onAuthStateChanged(callback: (user: User | null) => void) {
    if (!this.#auth) {
      // If not configured, we never authenticate.
      callback(null);
      return () => {};
    }
    return onAuthStateChanged(this.#auth, callback);
  }

  async getToken(): Promise<string | null> {
    if (!this.#auth || !this.#auth.currentUser) return null;
    return this.#auth.currentUser.getIdToken();
  }
}
