declare module 'tweetnacl' {
    export interface BoxKeyPair {
        publicKey: Uint8Array;
        secretKey: Uint8Array;
    }

    export function randomBytes(length: number): Uint8Array;

    export const box: {
        keyPair: {
            (): BoxKeyPair;
            fromSecretKey(secretKey: Uint8Array): BoxKeyPair;
        };
        (message: Uint8Array, nonce: Uint8Array, publicKey: Uint8Array, secretKey: Uint8Array): Uint8Array;
        open: (message: Uint8Array, nonce: Uint8Array, publicKey: Uint8Array, secretKey: Uint8Array) => Uint8Array | null;
        nonceLength: number;
        publicKeyLength: number;
        secretKeyLength: number;
        sharedKeyLength: number;
        overheadLength: number;
    };

    export const secretbox: {
        (message: Uint8Array, nonce: Uint8Array, key: Uint8Array): Uint8Array;
        open: (box: Uint8Array, nonce: Uint8Array, key: Uint8Array) => Uint8Array | null;
        keyLength: number;
        nonceLength: number;
        overheadLength: number;
    };
}
