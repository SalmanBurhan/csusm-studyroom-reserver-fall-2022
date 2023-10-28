import pyotp


def generate_code(token_file):

    f = open(token_file, "r+")
    secret = f.readline()[0:-1]
    offset = f.tell()
    count = int(f.readline())

    hotp = pyotp.HOTP(secret)
    code = hotp.at(count)

    f.seek(offset)
    f.write(str(count + 1))
    f.close()

    return code
