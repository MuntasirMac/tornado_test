from tinyec import registry
from Crypto.Cipher import AES
import hashlib, secrets, binascii

def encrypt_AES_GCM(msg, secretKey):
    aesCipher = AES.new(secretKey, AES.MODE_GCM)
    ciphertext, authTag = aesCipher.encrypt_and_digest(msg)
    return (ciphertext, aesCipher.nonce, authTag)

def decrypt_AES_GCM(ciphertext, nonce, authTag, secretKey):
    aesCipher = AES.new(secretKey, AES.MODE_GCM, nonce)
    plaintext = aesCipher.decrypt_and_verify(ciphertext, authTag)
    return plaintext

def ecc_point_to_256_bit_key(point):
    sha = hashlib.sha256(int.to_bytes(point.x, 32, 'big'))
    sha.update(int.to_bytes(point.y, 32, 'big'))
    return sha.digest()

curve = registry.get_curve('brainpoolP256r1')

def encrypt_ECC(msg, pubKey):
    ciphertextPrivKey = secrets.randbelow(curve.field.n)
    sharedECCKey = ciphertextPrivKey * pubKey
    secretKey = ecc_point_to_256_bit_key(sharedECCKey)
    ciphertext, nonce, authTag = encrypt_AES_GCM(msg, secretKey)
    ciphertextPubKey = ciphertextPrivKey * curve.g
    return (ciphertext, nonce, authTag, ciphertextPubKey)

def decrypt_ECC(encryptedMsg, privKey):
    (ciphertext, nonce, authTag, ciphertextPubKey) = encryptedMsg
    sharedECCKey = privKey * ciphertextPubKey
    secretKey = ecc_point_to_256_bit_key(sharedECCKey)
    plaintext = decrypt_AES_GCM(ciphertext, nonce, authTag, secretKey)
    return plaintext

# msg = 'c410daf69132ac67b295d1ca3038aa23'
# msg = msg.encode('utf-8')
# print("original msg:", msg)
# privKey = secrets.randbelow(curve.field.n)
# privKey = 33644979936982833300307455111916233314960809742751524519752293259244201947522
# pubKey = privKey * curve.g

# print("private key: ", type(privKey))
# print("public key: ", type(pubKey))

# encryptedMsg = encrypt_ECC(msg, pubKey)
# # encryptedMsg = list(encryptedMsg)
# print((encryptedMsg))
# encryptedMsgObj = {
#     'ciphertext': binascii.hexlify(encryptedMsg[0]),
#     'nonce': binascii.hexlify(encryptedMsg[1]),
#     'authTag': binascii.hexlify(encryptedMsg[2]),
#     'ciphertextPubKey': hex(encryptedMsg[3].x) + hex(encryptedMsg[3].y % 2)[2:]
# }
# print("encrypted msg:", encryptedMsgObj)

# decryptedMsg = decrypt_ECC(encryptedMsg, privKey)
# print("decrypted msg:", decryptedMsg)
# print("decrypted msg:", decryptedMsg.decode('utf-8'))