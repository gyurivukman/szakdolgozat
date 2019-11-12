import sys, json, os, math, re

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class AESFileCipher():

    def __init__(self, keys):
        self.__keys = keys
        self.__part_count = len(keys)
        self.__normal_read_size = AES.block_size -1
    
    def encryptFile(self, file_name):
        file_size = int(os.stat(file_name)[6])
        remainder_part_size = file_size%self.__part_count
        uniform_whole_part_size = int((file_size - remainder_part_size)/self.__part_count)

        with open(file_name, 'rb') as source:
            for key, index in zip(self.__keys, range(0, self.__part_count)):
                cipher = AES.new(key, AES.MODE_CBC)
                part_id_padding = "0" * (len(str(self.__part_count)) - len(str(index + 1)))
                part_id = f"{part_id_padding}{index + 1}" if (index < self.__part_count - 1) else (index + 1)
                file_part_name = f"{file_name}__{part_id}__{self.__part_count}.enc"
                with open(file_part_name, 'wb') as target:
                    target.write(cipher.iv)
                    current_part_size = uniform_whole_part_size + remainder_part_size if index == 0 else uniform_whole_part_size
                    if current_part_size < AES.block_size:
                        raw_chunk = source.read(current_part_size)
                        encoded_chunk = cipher.encrypt(pad(raw_chunk, AES.block_size))
                        target.write(encoded_chunk)
                    else:
                        whole_chunk_count = math.floor(current_part_size/self.__normal_read_size)
                        partial_chunk_size = current_part_size - (whole_chunk_count * self.__normal_read_size)
                        for j in range(0, whole_chunk_count):
                            raw_chunk = source.read(self.__normal_read_size)
                            if raw_chunk:
                                encoded_chunk = cipher.encrypt(pad(raw_chunk, AES.block_size))
                                target.write(encoded_chunk)
                        if partial_chunk_size > 0:
                            partial_raw_chunk = source.read(partial_chunk_size)
                            encoded_chunk = cipher.encrypt(pad(partial_raw_chunk, AES.block_size))
                            target.write(encoded_chunk)

    def decrypFile(self, target_file):
        pattern = f"^{target_file}__[0-9]+__[0-9]+\.enc$"
        file_fragments = [file_name for file_name in os.listdir() if re.match(pattern, file_name)]
        file_fragments.sort()
        print(f"Found the following file_fragments: {file_fragments}")
        with open(target_file, 'wb') as target:
            for fragment, key in zip(file_fragments, self.__keys):
                with open(fragment, 'rb') as encoded_source:
                    cipher = cipher = AES.new(key, AES.MODE_CBC, encoded_source.read(AES.block_size))
                    raw_chunk = encoded_source.read(AES.block_size)
                    while raw_chunk:
                        decoded_chunk = cipher.decrypt(raw_chunk)
                        target.write(unpad(decoded_chunk, AES.block_size))
                        raw_chunk = encoded_source.read(AES.block_size)


class AESMessageCipher():
    __key = None
    def __init__(self, )

if __name__ == "__main__":
    operation = sys.argv[1]
    target_file = sys.argv[2]
    keys = [b"AESEncryptionKey", b"LowFastKaviccsal",b"AESEncryptionKey", b"LowFastKaviccsal",b"AESEncryptionKey"]
    encryptionService = AESFileCipher(keys)

    if operation[1] == "e":
        encryptionService.encryptFile(target_file)
    else:
        encryptionService.decrypFile(target_file)
