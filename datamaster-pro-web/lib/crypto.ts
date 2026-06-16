/**
 * Criptografia de cookies usando AES-256-GCM (Web Crypto API).
 * Disponível no Edge Runtime do Next.js middleware.
 */

const ALGORITHM = 'AES-GCM'
const KEY_LENGTH = 256
const IV_LENGTH = 12
const TAG_LENGTH = 128

function getSecretKey(): string {
  const secret = process.env.COOKIE_ENCRYPTION_KEY
  if (!secret || secret.length < 32) {
    throw new Error(
      'COOKIE_ENCRYPTION_KEY deve ter pelo menos 32 caracteres. ' +
      'Gere com: openssl rand -hex 32'
    )
  }
  return secret
}

async function deriveKey(secret: string): Promise<CryptoKey> {
  const encoder = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  )

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: encoder.encode('dm-pro-cookie-salt-v1'),
      iterations: 100000,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: ALGORITHM, length: KEY_LENGTH },
    false,
    ['encrypt', 'decrypt']
  )
}

export async function encryptCookie(value: string): Promise<string> {
  const key = await deriveKey(getSecretKey())
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH))
  const encoder = new TextEncoder()

  const encrypted = await crypto.subtle.encrypt(
    { name: ALGORITHM, iv, tagLength: TAG_LENGTH },
    key,
    encoder.encode(value)
  )

  // Combina IV + dados criptografados em base64url
  const combined = new Uint8Array(iv.length + encrypted.byteLength)
  combined.set(iv, 0)
  combined.set(new Uint8Array(encrypted), iv.length)

  return uint8ToBase64Url(combined)
}

export async function decryptCookie(encryptedValue: string): Promise<string | null> {
  try {
    const key = await deriveKey(getSecretKey())
    const combined = base64UrlToUint8(encryptedValue)

    const iv = combined.slice(0, IV_LENGTH)
    const data = combined.slice(IV_LENGTH)

    const decrypted = await crypto.subtle.decrypt(
      { name: ALGORITHM, iv, tagLength: TAG_LENGTH },
      key,
      data
    )

    return new TextDecoder().decode(decrypted)
  } catch {
    // Cookie corrompido ou chave errada
    return null
  }
}

/**
 * Gera um fingerprint do navegador baseado em características estáveis.
 * Usado para vincular a sessão ao dispositivo.
 */
export function generateBrowserFingerprint(): string {
  // No middleware (Edge Runtime), usamos um fingerprint mais simples
  // baseado em headers disponíveis
  return '' // Será preenchido pelo client-side
}

export async function encryptFingerprint(fp: string): Promise<string> {
  return encryptCookie(fp)
}

export async function decryptFingerprint(encrypted: string): Promise<string | null> {
  return decryptCookie(encrypted)
}

// --- Helpers de conversão Base64URL ---

function uint8ToBase64Url(bytes: Uint8Array): string {
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function base64UrlToUint8(value: string): Uint8Array {
  let base64 = value.replace(/-/g, '+').replace(/_/g, '/')
  while (base64.length % 4) {
    base64 += '='
  }
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}
