import sys, json, os, math, re, time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class AESFileCipher():

    def __init__(self, keys):
        self.__keys = keys
        self.__part_count = len(keys)
    
    def encryptFile(self, file_name):
        start = time.time()
        end = None
        file_size = int(os.stat(file_name)[6])

        with open(file_name, 'rb') as source:
            for key, index in zip(self.__keys, range(0, self.__part_count)):
                cipher = AES.new(key, AES.MODE_CFB)
                file_part_name = self.__build_file_part_name(file_name, index)
                with open(file_part_name, 'wb') as target:
                    target.write(cipher.iv)
                    raw_chunk = source.read(128)
                    while raw_chunk:
                        target.write(cipher.encrypt(raw_chunk))
                        raw_chunk=source.read(128)
        end = time.time()
        print(f"encryption duration: {end-start}")

    def decrypFile(self, target_file):
        pattern = f"^{target_file}__[0-9]+__[0-9]+\.enc$"
        file_fragments = [file_name for file_name in os.listdir() if re.match(pattern, file_name)]
        file_fragments.sort()
        print(f"Found the following file_fragments: {file_fragments}")

        with open(target_file, 'wb') as target:
            for fragment, key in zip(file_fragments, self.__keys):
                with open(fragment, 'rb') as encoded_source:
                    cipher = cipher = AES.new(key, AES.MODE_CFB, encoded_source.read(AES.block_size))
                    raw_chunk = encoded_source.read(128)
                    while raw_chunk:
                        decoded_chunk = cipher.decrypt(raw_chunk)
                        target.write(decoded_chunk)
                        raw_chunk = encoded_source.read(128)

    def __build_file_part_name(self, file_name, index):
        part_id_padding = "0" * (len(str(self.__part_count)) - len(str(index + 1)))
        part_id = f"{part_id_padding}{index + 1}" if (index < self.__part_count - 1) else (index + 1)
        return f"{file_name}__{part_id}__{self.__part_count}.enc"

if __name__ == "__main__":
    operation = sys.argv[1]
    target_file = sys.argv[2]
    keys = [b"AESEncryptionKey", b"LowFastKavitssal", b"AESEncryptionKey"]
    encryptionService = AESFileCipher(keys)

    if operation[1] == "e":
        encryptionService.encryptFile(target_file)
    else:
        encryptionService.decrypFile(target_file)
