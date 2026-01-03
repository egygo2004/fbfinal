import { Client, Databases, Storage, Account } from 'appwrite';

const client = new Client()
    .setEndpoint(import.meta.env.VITE_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1')
    .setProject(import.meta.env.VITE_APPWRITE_PROJECT_ID || '');

export const databases = new Databases(client);
export const storage = new Storage(client);
export const account = new Account(client);

// IDs for collections (must match setup_appwrite.py)
export const DB_ID = 'fina';
export const QUEUE_COLL_ID = 'numbers_queue';
export const PROXIES_COLL_ID = 'proxies'; // New collection
export const SETTINGS_COLL_ID = 'settings';
export const ASSETS_BUCKET_ID = 'finafb';
