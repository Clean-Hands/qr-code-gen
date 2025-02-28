from PIL import Image
from masks import QrMask

class GaloisField:
    def __init__(self):
        # initialize exp and log tables for GF(256)
        self.exp = [0] * 256
        self.log = [0] * 256
        
        # generate the exp and log tables
        value = 1
        for i in range(256):
            self.exp[i] = value
            if i < 255:  # for i = 255, leave log[0] = 0
                self.log[value] = i
            
            value = value << 1  # multiply by 2
            if value > 255:
                value ^= 0b100011101  # reduce using x^8 + x^4 + x^3 + x^2 + 1
    
    def multiply(self, a, b):
        if a == 0 or b == 0:
            return 0
        return self.exp[(self.log[a] + self.log[b]) % 255]
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero")
        if a == 0:
            return 0
        return self.exp[(self.log[a] - self.log[b] + 255) % 255]


    # multiply two polynomials in GF(256)
    # each polynomial is represented as a list of coefficients from highest to lowest degree
    def multiply_polynomials(self, poly1, poly2):
        result = [0] * (len(poly1) + len(poly2) - 1)
        
        # multiply each term of poly1 with each term of poly2
        for i, coeff1 in enumerate(poly1):
            for j, coeff2 in enumerate(poly2):
                # XOR is addition in GF(256)
                result[i + j] ^= self.multiply(coeff1, coeff2)
        
        return result

class ModuleArray:
    
    def __init__(self, pixel_arr, module_size):
        self.pixel_arr = pixel_arr
        self.module_size = module_size
        
    def set_pixel_arr(self, pixel_arr):
        self.pixel_arr = pixel_arr
        
    def get_pixel_arr(self):
        return self.pixel_arr

    def get_module(self, x, y):
        # convert module x, y coords to real pixel coords
        module_x = (x+1)*self.module_size
        module_y = (y+1)*self.module_size
        return self.pixel_arr[module_x,module_y]

    def update_module(self, x, y, value):
        # convert module x, y coords to real pixel coords
        module_x = (x+1)*self.module_size
        module_y = (y+1)*self.module_size
        # for every pixel within that module, change its value
        for i in range(module_x, module_x+self.module_size):
            for j in range(module_y, module_y+self.module_size):
                self.pixel_arr[i,j] = value


# create a generator polynomial for the specified number of error correction words
# returns coefficients from highest to lowest degree
def create_generator_polynomial(num_codewords, gf):
    # start with g(x) = (x - α^0)
    generator = [1, gf.exp[0]]
    
    # multiply by (x - α^i) for i from 1 to num_codewords-1
    for i in range(1, num_codewords):
        # create the term (x - α^i)
        term = [1, gf.exp[i]]
        # multiply the current generator polynomial by this term
        generator = gf.multiply_polynomials(generator, term)
    
    return generator


# calculate error correction codewords using polynomial division in GF(256)
def calculate_error_correction(message_ints, num_codewords, gf):
    # generate the appropriate generator polynomial
    generator_coeffs = create_generator_polynomial(num_codewords, gf)
    
    # pad message with zeros according to generator polynomial degree
    padding = [0] * (len(generator_coeffs) - 1)
    dividend = message_ints + padding
    
    # perform polynomial division
    for i in range(len(message_ints)):
        if dividend[i] != 0:
            factor = dividend[i]
            for j in range(len(generator_coeffs)):
                dividend[i + j] ^= gf.multiply(generator_coeffs[j], factor)
    
    # return the remainder (error correction codewords)
    return dividend[-len(padding):]



# =================================================================================================================
# ================================================ END FUNCTIONS ==================================================
# =================================================================================================================


# CLI Options:
# -e, --err-corr [level]: Level of error correction (L, M, Q, H)
# -d, --data [string]: data that should be encoded within the QR code
# -v, --version [version number]: override version number
# -m, --mask [mask number]: override mask number



FINDER_PATTERN = [[1,1,1,1,1,1,1],
                  [1,0,0,0,0,0,1],
                  [1,0,1,1,1,0,1],
                  [1,0,1,1,1,0,1],
                  [1,0,1,1,1,0,1],
                  [1,0,0,0,0,0,1],
                  [1,1,1,1,1,1,1]]

ALIGNMENT_PATTERN = [[1,1,1,1,1],
                     [1,0,0,0,1],
                     [1,0,1,0,1],
                     [1,0,0,0,1],
                     [1,1,1,1,1]]

# data = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
data = "Hello, world!"

MODE_BITS = "0100" # byte mode

char_count = f'{len(data):08b}' # for byte mode, char_count needs to be 8 bits long

# TODO: figure out which version we should use (https://www.thonky.com/qr-code-tutorial/data-encoding)
# We are going to use 1L for a proof of concept

VERSION_NUM = 1
ERR_CORR_LVL = 1 #L
MAX_DATA_BITS = 19 * 8 # 1L
NUM_OF_ERR_CORR_CODEWORDS = int(26 - (MAX_DATA_BITS/8)) # this is only for ver 1 QR codes


# convert the characters to ISO 8859-1 encoding
combined_enc_str = ""
for char in data:
    combined_enc_str += f'{ord(char):08b}'

data_bits = MODE_BITS + char_count + combined_enc_str

# add up to 4 zeroes as a terminator, making sure we don't go over the max length
i = 0
while i < 4 and len(data_bits) < MAX_DATA_BITS:
    data_bits += "0"
    i += 1

# make the length of the bitstring a multiple of 8
while len(data_bits) % 8 != 0:
    data_bits += "0"

# add padding bytes until we reach the required size
while len(data_bits) < MAX_DATA_BITS:
    data_bits += "1110110000010001"
# if we went over by one byte, remove the extra byte
if len(data_bits) > MAX_DATA_BITS:
    data_bits = data_bits[:-8]
    
assert len(data_bits) == MAX_DATA_BITS

message_ints = []
i = 0
while i < len(data_bits):
    message_ints.append(int(data_bits[i:i+8], 2))
    i += 8

# TODO: if we have a version high enough, break into blocks/groups

# initialize Galois Field
gf = GaloisField()

# calculate error correction codewords
error_corr_ints = calculate_error_correction(message_ints, NUM_OF_ERR_CORR_CODEWORDS, gf)

content_ints = message_ints + error_corr_ints

content_bits = ""
for cont_int in content_ints:
    content_bits += f'{cont_int:08b}'

MODULES_PER_EDGE = (((VERSION_NUM - 1) * 4) + 21)
IMAGE_RESOLUTION = 512

rounded_resolution = 0
while rounded_resolution < IMAGE_RESOLUTION:
    rounded_resolution += (MODULES_PER_EDGE+2)

module_size = int(rounded_resolution/(MODULES_PER_EDGE+2))

qr_image = Image.new(mode="P",size=[rounded_resolution, rounded_resolution], color="white")
pixel_arr = qr_image.load()

module_arr = ModuleArray(pixel_arr, module_size)

# Finder patterns
for x, row in enumerate(FINDER_PATTERN):
    for y, value in enumerate(row):
        module_arr.update_module(x, y, value)
for x, row in enumerate(FINDER_PATTERN):
    for y, value in enumerate(row):
        module_arr.update_module((MODULES_PER_EDGE-7)+x, y, value)
for x, row in enumerate(FINDER_PATTERN):
    for y, value in enumerate(row):
        module_arr.update_module(x, (MODULES_PER_EDGE-7)+y, value)

# Timing patterns
for x in range(7, MODULES_PER_EDGE-7):
    if x % 2 == 0:
        module_arr.update_module(x, 6, 1)
for y in range(7, MODULES_PER_EDGE-7):
    if y % 2 == 0:
        module_arr.update_module(6, y, 1)
        
# Dark module: one module that is ALWAYS dark in ALL QR codes
module_arr.update_module(8, ((4 * VERSION_NUM) + 9), 1)

# Add the data bits

data_list = [int(x) for x in list(content_bits)]

# Data bits under the top right finder pattern
for x in range(MODULES_PER_EDGE-1, MODULES_PER_EDGE-7, -4):
    for y in range(MODULES_PER_EDGE-1, 8, -1):
        module_arr.update_module(x, y, data_list.pop(0))
        module_arr.update_module(x-1, y, data_list.pop(0))
    for y in range(9, MODULES_PER_EDGE, 1):
        module_arr.update_module(x-2, y, data_list.pop(0))
        module_arr.update_module(x-3, y, data_list.pop(0))

# Data bits between the left and right finder paterns
for x in range(MODULES_PER_EDGE-9, 9, -4):
    for y in range(MODULES_PER_EDGE-1, -1, -1):
        if y == 6:
            continue
        module_arr.update_module(x, y, data_list.pop(0))
        module_arr.update_module(x-1, y, data_list.pop(0))
    for y in range(0, MODULES_PER_EDGE, 1):
        if y == 6:
            continue
        module_arr.update_module(x-2, y, data_list.pop(0))
        module_arr.update_module(x-3, y, data_list.pop(0))
        
# Data bits between the top left and bottom left finder paterns
for y in range(MODULES_PER_EDGE-9, 8, -1):
    module_arr.update_module(8, y, data_list.pop(0))
    module_arr.update_module(7, y, data_list.pop(0))
for y in range(9, MODULES_PER_EDGE-8, 1):
    module_arr.update_module(5, y, data_list.pop(0))
    module_arr.update_module(4, y, data_list.pop(0))
for y in range(MODULES_PER_EDGE-9, 8, -1):
    module_arr.update_module(3, y, data_list.pop(0))
    module_arr.update_module(2, y, data_list.pop(0))
for y in range(9, MODULES_PER_EDGE-8, 1):
    module_arr.update_module(1, y, data_list.pop(0))
    module_arr.update_module(0, y, data_list.pop(0))

# apply mask
qr_masks = QrMask(MODULES_PER_EDGE, ERR_CORR_LVL)
qr_image = qr_masks.apply_best_mask(qr_image, module_arr)

try:
    qr_image.save("./" + data + ".png")
except Exception as e:
    print("Error saving file:", e)
else:
    print("Output saved as ./" + data + ".png")



# TODO: if version > 7, we have to include the version number (https://www.thonky.com/qr-code-tutorial/format-version-information#version-information)