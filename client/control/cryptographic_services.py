import sys, json, os, math, re

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

key = b"AESEncryptionKey"

def encrypt_file(file_name, fragment_count=1):
    cipher = AES.new(key, AES.MODE_CBC)
    file_size = int(os.stat(file_name)[6])
    whole_fragment_size = math.ceil(file_size/fragment_count)
    whole_fragment_count = math.floor(file_size/whole_fragment_size)
    partial_fragment_size = file_size - (whole_fragment_size * whole_fragment_count)

    with open(file_name, 'rb') as source:
        for i in range (0, fragment_count):
            part_id_padding = (len(str(fragment_count)) - 1) * "0"
            part_id = f"{part_id_padding}{i+1}" if i<fragment_count-1 else i+1
            file_part_name = f"{file_name}__{part_id}__{fragment_count}.enc"
            with open(file_part_name, 'wb') as target:
                if i == 0:
                    target.write(cipher.iv)
                if whole_fragment_size < AES.block_size:
                    raw_chunk = source.read(whole_fragment_size)
                    encoded_chunk = cipher.encrypt(pad(raw_chunk, AES.block_size))
                    target.write(encoded_chunk)
                else:
                    chunk_count = None
                    if i == fragment_count - 1 and partial_fragment_size > 0:
                        chunk_count = math.ceil(partial_fragment_size/(AES.block_size -1))
                    else:
                        chunk_count = math.ceil(whole_fragment_size/(AES.block_size - 1))
                    for j in range(0, chunk_count):
                        raw_chunk = source.read(AES.block_size - 1)
                        if raw_chunk:
                            encoded_chunk = cipher.encrypt(pad(raw_chunk, AES.block_size))
                            target.write(encoded_chunk)

def decrypt_file(target_file):
    pattern = f"^{target_file}__[0-9]+__[0-9]+\.enc$"
    file_fragments = [file_name for file_name in os.listdir() if re.match(pattern, file_name)]
    file_fragments.sort()
    print(file_fragments)
    with open(target_file, 'wb') as target:
        cipher = None
        for fragment in file_fragments:
            with open(fragment, 'rb') as encoded_source:
                if not cipher:
                    cipher = AES.new(key, AES.MODE_CBC, encoded_source.read(AES.block_size))
                fragment_size = int(os.stat(fragment)[6])
                raw_chunk = encoded_source.read(AES.block_size)
                while raw_chunk:
                    decoded_chunk = cipher.decrypt(raw_chunk)
                    target.write(unpad(decoded_chunk, AES.block_size))
                    raw_chunk = encoded_source.read(AES.block_size)

if __name__ == "__main__":
    operation = sys.argv[1]
    target_file = sys.argv[2]
    if operation[1] == "e":
        fragment_count = int(sys.argv[3])
        encrypt_file(target_file, fragment_count)
    else:
        decrypt_file(target_file)
