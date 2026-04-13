import sys
import base64
import os

def encode_gsm(code):
    b64 = base64.b64encode(code.encode('utf-8'))
    bin_str = "".join(f"{b:08b}" for b in b64)
    return base64.b32encode(bin_str.encode('utf-8')).decode('utf-8')

def decode_gsm(gsm_code):
    bin_str = base64.b32decode(gsm_code.encode('utf-8')).decode('utf-8')
    byte_array = bytearray()
    for i in range(0, len(bin_str), 8):
        byte_array.append(int(bin_str[i:i+8], 2))
    return base64.b64decode(byte_array).decode('utf-8')

def main():
    if len(sys.argv) < 2:
        print("Goosembler v1.0")
        print("Usage:")
        print("  gsm compile <file.py>  - Compile to .gsm")
        print("  gsm <file.gsm>         - Run .gsm file")
        return

    cmd = sys.argv[1]

    if cmd == "compile":
        if len(sys.argv) < 3:
            print("Error: Provide a .py file")
            return

        input_file = sys.argv[2]
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            code = f.read()

        output_file = input_file.replace('.py', '.gsm')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encode_gsm(code))
        print(f"[*] Compiled: {output_file}")

    else:
        filename = cmd
        if not os.path.exists(filename):
            print(f"Error: File {filename} not found")
            return

        with open(filename, 'r', encoding='utf-8') as f:
            gsm_code = f.read()

        try:
            py_code = decode_gsm(gsm_code)
            exec(py_code, {"__name__": "__main__"})
        except Exception as e:
            print(f"Goosembler Error: {e}")

if __name__ == "__main__":
    main()
