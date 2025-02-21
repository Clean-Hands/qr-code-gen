from PIL import Image
import numpy

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

# TODO: put the following two functions in a class where pixel_arr and module_size are instance variables

def get_module(x, y):
    global pixel_arr, module_size
    # convert module x, y coords to real pixel coords
    module_x = (x+1)*module_size
    module_y = (y+1)*module_size
    return pixel_arr[module_x,module_y]

def update_module(x, y, value):
    global pixel_arr, module_size
    # convert module x, y coords to real pixel coords
    module_x = (x+1)*module_size
    module_y = (y+1)*module_size
    # for every pixel within that module, change its value
    for i in range(module_x, module_x+module_size):
        for j in range(module_y, module_y+module_size):
            pixel_arr[i,j] = value


def mask_num_0(column, row):
    module_val = get_module(column, row)
    if (row + column) % 2 == 0:
        return not module_val
    else:
        return module_val

def mask_num_1(column, row):
    module_val = get_module(column, row)
    if row % 2 == 0:
        return not module_val
    else:
        return module_val

def mask_num_2(column, row):
    module_val = get_module(column, row)
    if column % 3 == 0:
        return not module_val
    else:
        return module_val

def mask_num_3(column, row):
    module_val = get_module(column, row)
    if (row + column) % 3 == 0:
        return not module_val
    else:
        return module_val

def mask_num_4(column, row):
    module_val = get_module(column, row)
    if (numpy.floor(row/2) + numpy.floor(column/3)) % 2 == 0:
        return not module_val
    else:
        return module_val

def mask_num_5(column, row):
    module_val = get_module(column, row)
    if ((row * column) % 2) + ((row * column) % 3) == 0:
        return not module_val
    else:
        return module_val

def mask_num_6(column, row):
    module_val = get_module(column, row)
    if (((row * column) % 2) + ((row * column) % 3)) % 2 == 0:
        return not module_val
    else:
        return module_val

def mask_num_7(column, row):
    module_val = get_module(column, row)
    if (((row + column) % 2) + ((row * column) % 3)) % 2 == 0:
        return not module_val
    else:
        return module_val


def apply_mask(mask_func):
    
    # Data bits under the top right finder pattern
    for x in range(MODULES_PER_EDGE-8, MODULES_PER_EDGE, 1):
        for y in range(9, MODULES_PER_EDGE, 1):
            update_module(x, y, mask_func(x, y))
            
    # Data bits between the left and right finder paterns
    for x in range(9, MODULES_PER_EDGE-8, 1):
        for y in range(0, MODULES_PER_EDGE, 1):
            if y == 6:
                continue
            update_module(x, y, mask_func(x, y))
            
    # Data bits between the top left and bottom left finder paterns
    for y in range(9, MODULES_PER_EDGE-8, 1):
        update_module(8, y, mask_func(8, y))
        update_module(7, y, mask_func(7, y))
    for x in range(0, 6, 1):
        for y in range(9, MODULES_PER_EDGE-8, 1):
            update_module(x, y, mask_func(x, y))
    
    return

def eval_condition_1():
    # Evaluation Condition #1: 5+ same-colored modules in a row/column
    penalty = 0
    prev_column = [-1] * MODULES_PER_EDGE
    consecutive_count_column = [1] * MODULES_PER_EDGE
    
    for x in range(0, MODULES_PER_EDGE):
        consecutive_count = 1
        prev_module = -1

        for y in range(0, MODULES_PER_EDGE):
            curr_module = get_module(x, y)
            
            # if the current module is the same color as the previous one, update consecutive_count
            if curr_module == prev_module:
                consecutive_count += 1
                # if we have 5 modules with the same color in a row, add 3 to the penalty
                if consecutive_count == 5:
                    penalty += 3
                # for every same-colored module after the 5th, add one extra penalty point
                elif consecutive_count > 5:
                    penalty += 1
            # if it is a different color, reset the count
            else:
                consecutive_count = 1
                
            # if the current module is the same color as the previous one, update consecutive_count
            if curr_module == prev_column[y]:
                consecutive_count_column[y] += 1
                # if we have 5 modules with the same color in a column, add 3 to the penalty
                if consecutive_count_column[y] == 5:
                    penalty += 3
                # for every same-colored module after the 5th, add one extra penalty point
                elif consecutive_count_column[y] > 5:
                    penalty += 1
            # if it is a different color, reset the count
            else:
                consecutive_count_column[y] = 1

            # update the value of the previous module
            prev_module = curr_module
            prev_column[y] = curr_module

    return penalty

def eval_condition_2():
    # Evaluation Condition #2: 2x2 squares of the same color
    penalty = 0
    for x in range(0, MODULES_PER_EDGE-1):
        for y in range(0, MODULES_PER_EDGE-1):
            if get_module(x, y) == get_module(x+1, y) == get_module(x, y+1) == get_module(x+1, y+1):
                penalty += 3
    return penalty

def eval_condition_3():
    # Evaluation Condition #3: patterns of dark-light-dark-dark-dark-light-dark with 4 light on either side
    patt_1 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
    patt_2 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    patt_len = len(patt_1)
    
    penalty = 0
    for x in range(0, MODULES_PER_EDGE-9):
        for y in range(0, MODULES_PER_EDGE-9):
            test_list_vert = []
            test_list_horz = []
            for i in range(patt_len):
                test_list_vert.append(get_module(x, y+i))
                test_list_horz.append(get_module(x+i, y))
            if test_list_vert == patt_1 or test_list_vert == patt_2:
                penalty += 40
            if test_list_horz == patt_1 or test_list_horz == patt_2:
                penalty += 40
                
    return penalty

def eval_condition_4():
    # Evaluation Condition #4: ratio of black to white modules 
    
    dark_count = 0
    total_module_count = MODULES_PER_EDGE * MODULES_PER_EDGE
    for x in range(0, MODULES_PER_EDGE):
        for y in range(0, MODULES_PER_EDGE):
            if get_module(x, y) == 1:
                dark_count += 1

    dark_percent = (dark_count/total_module_count) * 100
    distance_from_equal = int(abs(dark_percent - 50))
    
    mult = 0
    while (distance_from_equal-1) > mult:
        mult += 1

    return mult * 10

def calc_mask_score():
    penalty = eval_condition_1()
    penalty += eval_condition_2()
    penalty += eval_condition_3()
    penalty += eval_condition_4()
    return penalty
            

def add_format_bits(err_corr_lvl, mask_ver):
    ec_lvl_bits = f'{err_corr_lvl:02b}'
    mask_ver_bits = f'{mask_ver:03b}'
    format_bits = ec_lvl_bits + mask_ver_bits
    
    gen_poly_int = 0b10100110111
    mask = 0b100000000000000
    ten_mask_max = 0b111110000000000
    
    parity_bits = format_bits
    
    # make the string 15 bits long
    while len(parity_bits) < 15:
        parity_bits += "0"
    
    parity_int = int(parity_bits, 2)
    
    # while the bitstring of parity_int is longer than 10 bits, XOR it with generator polynomial
    while parity_int & ten_mask_max != 0:
        gen_poly_int_temp = gen_poly_int
    
        # get the position of the most significant bit in parity_int
        while mask & parity_int == 0:
            mask = mask >> 1
        
        # resize gen_poly_int_temp to match the size of parity_int
        while mask & gen_poly_int_temp == 0:
            gen_poly_int_temp = gen_poly_int_temp << 1
        
        # XOR the parity int with the generator polynomial
        parity_int = parity_int ^ gen_poly_int_temp
    
    format_bits += f'{parity_int:010b}'
    
    format_bits = f'{(0b101010000010010 ^ int(format_bits, 2)):015b}'
    assert len(format_bits) == 15
    
    # add the format bits to the QR code
    format_list = [int(i) for i in list(format_bits)]
    for y in range(MODULES_PER_EDGE-1, MODULES_PER_EDGE-8, -1):
        update_module(8, y, format_list.pop(0))
    for y in range(8, -1, -1):
        if y == 6: continue
        update_module(8, y, format_list.pop(0))

    format_list = [int(i) for i in list(format_bits)]
    for x in range(0, 6, 1):
        update_module(x, 8, format_list.pop(0))
    update_module(7, 8, format_list.pop(0))
    for x in range(MODULES_PER_EDGE-8, MODULES_PER_EDGE, 1):
        update_module(x, 8, format_list.pop(0))



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


# Finder patterns
for x, row in enumerate(FINDER_PATTERN):
    for y, value in enumerate(row):
        update_module(x, y, value)
for x, row in enumerate(FINDER_PATTERN):
    for y, value in enumerate(row):
        update_module((MODULES_PER_EDGE-7)+x, y, value)
for x, row in enumerate(FINDER_PATTERN):
    for y, value in enumerate(row):
        update_module(x, (MODULES_PER_EDGE-7)+y, value)

# Timing patterns
for x in range(7, MODULES_PER_EDGE-7):
    if x % 2 == 0:
        update_module(x, 6, 1)
for y in range(7, MODULES_PER_EDGE-7):
    if y % 2 == 0:
        update_module(6, y, 1)
        
# Dark module: one module that is ALWAYS dark in ALL QR codes
update_module(8, ((4 * VERSION_NUM) + 9), 1)

# Add the data bits

data_list = [int(x) for x in list(content_bits)]

# Data bits under the top right finder pattern
for x in range(MODULES_PER_EDGE-1, MODULES_PER_EDGE-7, -4):
    for y in range(MODULES_PER_EDGE-1, 8, -1):
        update_module(x, y, data_list.pop(0))
        update_module(x-1, y, data_list.pop(0))
    for y in range(9, MODULES_PER_EDGE, 1):
        update_module(x-2, y, data_list.pop(0))
        update_module(x-3, y, data_list.pop(0))

# Data bits between the left and right finder paterns
for x in range(MODULES_PER_EDGE-9, 9, -4):
    for y in range(MODULES_PER_EDGE-1, -1, -1):
        if y == 6:
            continue
        update_module(x, y, data_list.pop(0))
        update_module(x-1, y, data_list.pop(0))
    for y in range(0, MODULES_PER_EDGE, 1):
        if y == 6:
            continue
        update_module(x-2, y, data_list.pop(0))
        update_module(x-3, y, data_list.pop(0))
        
# Data bits between the top left and bottom left finder paterns
for y in range(MODULES_PER_EDGE-9, 8, -1):
    update_module(8, y, data_list.pop(0))
    update_module(7, y, data_list.pop(0))
for y in range(9, MODULES_PER_EDGE-8, 1):
    update_module(5, y, data_list.pop(0))
    update_module(4, y, data_list.pop(0))
for y in range(MODULES_PER_EDGE-9, 8, -1):
    update_module(3, y, data_list.pop(0))
    update_module(2, y, data_list.pop(0))
for y in range(9, MODULES_PER_EDGE-8, 1):
    update_module(1, y, data_list.pop(0))
    update_module(0, y, data_list.pop(0))


# apply masks

# make copies of the original unmasked QR code
qr_image_mask_0 = qr_image.copy()
qr_image_mask_1 = qr_image.copy()
qr_image_mask_2 = qr_image.copy()
qr_image_mask_3 = qr_image.copy()
qr_image_mask_4 = qr_image.copy()
qr_image_mask_5 = qr_image.copy()
qr_image_mask_6 = qr_image.copy()
qr_image_mask_7 = qr_image.copy()

# mask 0
pixel_arr = qr_image_mask_0.load()
apply_mask(mask_num_0)
add_format_bits(ERR_CORR_LVL, 0)
min_mask_score = calc_mask_score()
qr_image = qr_image_mask_0

# mask 1
pixel_arr = qr_image_mask_1.load()
apply_mask(mask_num_1)
add_format_bits(ERR_CORR_LVL, 1)
mask_score = calc_mask_score()
if mask_score < min_mask_score:
    min_mask_score = mask_score
    qr_image = qr_image_mask_1

# mask 2
pixel_arr = qr_image_mask_2.load()
apply_mask(mask_num_2)
add_format_bits(ERR_CORR_LVL, 2)
mask_score = calc_mask_score()
if mask_score < min_mask_score:
    min_mask_score = mask_score
    qr_image = qr_image_mask_2

# mask 3
pixel_arr = qr_image_mask_3.load()
apply_mask(mask_num_3)
add_format_bits(ERR_CORR_LVL, 3)
mask_score = calc_mask_score()
if mask_score < min_mask_score:
    min_mask_score = mask_score
    qr_image = qr_image_mask_3

# mask 4
pixel_arr = qr_image_mask_4.load()
apply_mask(mask_num_4)
add_format_bits(ERR_CORR_LVL, 4)
mask_score = calc_mask_score()
if mask_score < min_mask_score:
    min_mask_score = mask_score
    qr_image = qr_image_mask_4

# mask 5
pixel_arr = qr_image_mask_5.load()
apply_mask(mask_num_5)
add_format_bits(ERR_CORR_LVL, 5)
mask_score = calc_mask_score()
if mask_score < min_mask_score:
    min_mask_score = mask_score
    qr_image = qr_image_mask_5

# mask 6
pixel_arr = qr_image_mask_6.load()
apply_mask(mask_num_6)
add_format_bits(ERR_CORR_LVL, 6)
mask_score = calc_mask_score()
if mask_score < min_mask_score:
    min_mask_score = mask_score
    qr_image = qr_image_mask_6

# mask 7
pixel_arr = qr_image_mask_7.load()
apply_mask(mask_num_7)
add_format_bits(ERR_CORR_LVL, 7)
mask_score = calc_mask_score()
if mask_score < min_mask_score:
    min_mask_score = mask_score
    qr_image = qr_image_mask_7

try:
    qr_image.save("./" + data + ".png")
except Exception as e:
    print("Error saving file:", e)
else:
    print("QR code image saved as ./" + data + ".png")



# TODO: if version > 7, we have to include the version number (https://www.thonky.com/qr-code-tutorial/format-version-information#version-information)