import base64
import ctypes
from random import Random, randbytes, randint
from struct import pack

# 4D356F584146706Ah


class GoldMax:

    def __init__(self):
        self.shared_secret = b"\x6A\x70\x46\x41\x58\x6F\x35\x4D"
        self.session_key = b"Dont_Forget_To_Encrypt_Please!!!"
        self.control_cookie = "48WxLONKwJEo="
        self.state = {
            "Authenticate": self.control_cookie + "wGMEvMwBW77HDj",
            "KeyExchange": self.control_cookie + "ndB3gbMjL",
            "Ready": [';'],
            "AgentId": "XCghVFFHyAYREhsB=",
            "Campaign": "i19TotqC9iD8Y0B7jcGnpp5hYcyjg4cL"
        }
        self.commands = {
            "Idle": "",
            "Execute": "",
            "Start": "",
            "Read": "",
            "Update": "",
            "Write": {"Cmd": "",
                      "Wget": self.control_cookie + "",
                      "CleanFile": self.control_cookie + "",
                      "DestinationFile": "",
                      },
        }

    @staticmethod
    def custom_base64_encode(blob):
        """
        Used to encode RSA key
        """
        custom_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        standard_base = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

        # Add Padding -- The padding is stripped so this is needed or else it will fail
        if not isinstance(blob, bytes):
            blob = blob.encode()

        encoded = base64.b64encode(blob, altchars=b'-_')
        encoded = encoded.strip(b'=')

        return encoded

    @staticmethod
    def custom_base64_decode(encoded_blob):
        """
        Used to decode custom base64 implementation
        """
        custom_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        standard_base = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

        if isinstance(encoded_blob, bytes):
            encoded_blob = encoded_blob.decode()
        # Add Padding -- The padding is stripped so this is needed or else it will fail
        decoded = base64.b64decode(encoded_blob + "===", altchars='-_')

        return decoded

    @staticmethod
    def aes_encrypt_cfb(plaintext: bytes, key: bytes):
        """
        plaintext: bytes: Message to be encrypted
        key:       bytes: AES Encryption key (32 bytes)
        iv:        bytes: AES IV (16 bytes)
        """
        lib = ctypes.cdll.LoadLibrary("./toolbox/GoldenCrypto.so")

        # AES imports
        aes_encrypt = lib.encrypt_AES_CFB
        aes_encrypt.argtypes = [ctypes.c_char_p]
        aes_encrypt.restype = ctypes.c_void_p
        free = lib.free
        free.argtypes = [ctypes.c_void_p]

        if len(key) != 32:
            print("Invalid Key! Must be 32 bytes!")
            return ""
        # Verify we got a good payload
        ptr = aes_encrypt(plaintext, key)

        cipher_text = ctypes.string_at(ptr)

        free(ptr)

        return cipher_text

    @staticmethod
    def aes_decrypt_cfb(ciphertext: bytes, key: bytes):
        """
        plaintext: bytes: Message to be decrypted
        key:       bytes: AES Encryption key (32 bytes)
        iv:        bytes: AES IV (16 bytes)
        """
        lib = ctypes.cdll.LoadLibrary("./toolbox/GoldenCrypto.so")
        aes_decrypt = lib.decrypt_AES_CFB
        aes_decrypt.argtypes = [ctypes.c_char_p]
        aes_decrypt.restype = ctypes.c_void_p
        free = lib.free
        free.argtypes = [ctypes.c_void_p]

        if len(key) != 32:
            print("Invalid Key! Must be 32 bytes!")
            return ""

        ptr = aes_decrypt(ciphertext, len(ciphertext), key)

        decrypted = ctypes.string_at(ptr)

        free(ptr)

        return decrypted

    @staticmethod
    def rsa_encrypt_oaep(plaintext: bytes):
        """
        Utilizes the RSA OAEP padding scheme
        Performs encryption using Golang to generate Public Key from Private (extracted from sample)
        """

        lib = ctypes.cdll.LoadLibrary("./toolbox/GoldenCrypto.so")
        # RSA imports
        rsa_encrypt = lib.encrypt_RSA_OAEP
        rsa_encrypt.argtypes = [ctypes.c_char_p]
        rsa_encrypt.restype = ctypes.c_void_p
        free = lib.free
        free.argtypes = [ctypes.c_void_p]

        while True:
            ptr = rsa_encrypt(plaintext)

            encrypted = ctypes.string_at(ptr)

            free(ptr)
            if len(encrypted) >= 100:
                break

        return encrypted

    @staticmethod
    def rsa_decrypt_oaep(ciphertext: bytes):
        """
        Utilizes the extracted private key for decryption
        """
        lib = ctypes.cdll.LoadLibrary("./toolbox/GoldenCrypto.so")
        rsa_decrypt = lib.decrypt_RSA_OAEP
        rsa_decrypt.argtypes = [ctypes.c_char_p]
        free = lib.free
        

        print("About to decrypt..")
        ptr = rsa_decrypt(ciphertext)
        print("After decrypt")
        decrypted = ctypes.string_at(ptr)
        
        free(ptr)

        return decrypted

    def get_session_key(self):
        """
        Return Session encrypted with RSA key
        """
        while True:
            encrypted_session_token = self.rsa_encrypt_oaep(self.session_key)
            print(len(encrypted_session_token))

            # Sometimes the size is less than 256 which the implant will throw away
            if len(encrypted_session_token) == 256:
                encoded_token = base64.b64encode(encrypted_session_token)
                return encoded_token

