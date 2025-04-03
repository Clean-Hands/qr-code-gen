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
    
    def __init__(self, pixel_arr, version_num, modules_per_edge, module_size):
        self.pixel_arr = pixel_arr
        self.version_num = version_num
        self.modules_per_edge = modules_per_edge
        self.module_size = module_size
        self.protected_modules = []
        self.FINDER_PATTERN = [[0,0,0,0,0,0,0,0,0],
                               [0,1,1,1,1,1,1,1,0],
                               [0,1,0,0,0,0,0,1,0],
                               [0,1,0,1,1,1,0,1,0],
                               [0,1,0,1,1,1,0,1,0],
                               [0,1,0,1,1,1,0,1,0],
                               [0,1,0,0,0,0,0,1,0],
                               [0,1,1,1,1,1,1,1,0],
                               [0,0,0,0,0,0,0,0,0]]
        self.ALIGNMENT_PATTERN = [[1,1,1,1,1],
                                  [1,0,0,0,1],
                                  [1,0,1,0,1],
                                  [1,0,0,0,1],
                                  [1,1,1,1,1]]
        
        # Currently only has data for versions 2 - 6
        self.ALIGNMENT_PATTERN_LOCS = [18, 22, 26, 30, 34]
        
        self.add_finder_patterns()
        self.add_timing_patterns()
        self.add_dark_module()
        self.protect_format_bits()
        if self.version_num > 1:
            self.add_alignment_patterns()
        
    def set_pixel_arr(self, pixel_arr):
        self.pixel_arr = pixel_arr
        
    def get_pixel_arr(self):
        return self.pixel_arr

    def get_module(self, x, y):
        # convert module x, y coords to real pixel coords
        module_x = (x+1)*self.module_size
        module_y = (y+1)*self.module_size
        return self.pixel_arr[module_x, module_y]

    def update_module(self, x, y, value, force=False):
        # if we are not allowed to update this module, return error        
        if [x, y] in self.protected_modules and not force:
            return 1
        # convert module x, y coords to real pixel coords
        module_x = (x+1)*self.module_size
        module_y = (y+1)*self.module_size
        # for every pixel within that module, change its value
        for i in range(module_x, module_x+self.module_size):
            for j in range(module_y, module_y+self.module_size):
                self.pixel_arr[i,j] = value
        return 0
    
    def add_finder_patterns(self):
        # Finder patterns
        for x, row in enumerate(self.FINDER_PATTERN):
            for y, value in enumerate(row):
                # Top left finder pattern
                self.update_module(x-1, y-1, value)
                self.protected_modules.append([x-1, y-1])
                # Top right finder pattern
                self.update_module((self.modules_per_edge-7)+x-1, y-1, value)
                self.protected_modules.append([(self.modules_per_edge-7)+x-1, y-1])
                # Bottom left finder pattern
                self.update_module(x-1, (self.modules_per_edge-7)+y-1, value)
                self.protected_modules.append([x-1, (self.modules_per_edge-7)+y-1])
    
    def protect_format_bits(self):
        if self.version_num > 6:
            #TODO: different format bit location
            pass
        else:
             # format bits to the right of the bottom-left finder pattern
            for y in range(0, self.modules_per_edge, 1):
                if y not in range(9, self.modules_per_edge-8):
                    # self.update_module(8, y, 1, True)
                    self.protected_modules.append([8, y])
            
            # format bits under the top left finder pattern
            for x in range(0, self.modules_per_edge, 1):
                if x not in range(9, self.modules_per_edge-8):
                    # self.update_module(x, 8, 1, True)
                    self.protected_modules.append([x, 8])

    def add_timing_patterns(self):
        # Timing patterns
        for x in range(7, self.modules_per_edge-7):
            if x % 2 == 0:
                self.update_module(x, 6, 1, True)
            self.protected_modules.append([x, 6])
        for y in range(7, self.modules_per_edge-7):
            if y % 2 == 0:
                self.update_module(6, y, 1, True)
            self.protected_modules.append([6, y])
                
    # Dark module: one module that is ALWAYS dark in ALL QR codes
    def add_dark_module(self):
        self.update_module(8, ((4 * self.version_num) + 9), 1, True)
        self.protected_modules.append([8, ((4 * self.version_num) + 9) ])
    
    def add_alignment_patterns(self):
        pos = self.ALIGNMENT_PATTERN_LOCS[self.version_num-2]
        for x_shift, row in enumerate(self.ALIGNMENT_PATTERN):
            for y_shift, value in enumerate(row):
                align_x = pos + x_shift - 2
                align_y = pos + y_shift - 2
                self.update_module(align_x, align_y, value)
                self.protected_modules.append([align_x, align_y])



class MovableHeadArray:
    
    def __init__(self, data_bits):
        self.data_bits = data_bits
        self.curr_index = 0
        
    def get_head(self):
        try:
            # print(self.curr_index)
            return self.data_bits[self.curr_index]
        # If we try to get a bit after the end of the data bits, just return 0 
        except:
            return 0
        
    def inc_head(self):
        self.curr_index += 1
    
    def set_head(self, value):
        self.data_bits[self.curr_index] = value


# object that holds all the information about any specific version and error correction level QR code
class CodewordCounts:
    
    def __init__(self, groups, eccw_count):
        self.block_counts = []
        self.data_cw_counts = []
        self.max_data_bits = 0
        for group in groups:
            self.block_counts.append(group[0])
            self.data_cw_counts.append(group[1])
            self.max_data_bits += (group[0] * group[1])
        self.max_data_bits *= 8
        self.groups_count = len(groups)
        self.eccw_count = eccw_count
        
    def getECCWCount(self):
        return self.eccw_count
    def getGroupsCount(self):
        return self.groups_count
    def getBlocksCount(self, group_num):
        return self.block_counts[group_num]
    def getDataCWCount(self, group_num):
        return self.data_cw_counts[group_num]
    def getMaxDataBits(self):
        return self.max_data_bits
        


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


# TODO CLI Options:
# -e, --err-corr [level]: Level of error correction (L, M, Q, H)
# -d, --data [string]: data that should be encoded within the QR code
# -v, --version [version number]: override version number
# -m, --mask [mask number]: override mask number


# Currently only has data for versions 1 - 6
CODEWORD_BLOCKS = [[CodewordCounts([[1, 9]], 17),           # 1H
                    CodewordCounts([[1, 13]], 13),          # 1Q
                    CodewordCounts([[1, 16]], 10),          # 1M
                    CodewordCounts([[1, 19]], 7)],          # 1L

                   [CodewordCounts([[1, 16]], 28),          # 2H
                    CodewordCounts([[1, 22]], 22),          # 2Q
                    CodewordCounts([[1, 28]], 16),          # 2M
                    CodewordCounts([[1, 34]], 10)],         # 2L

                   [CodewordCounts([[2, 13]], 22),          # 3H
                    CodewordCounts([[2, 17]], 18),          # 3Q
                    CodewordCounts([[1, 44]], 26),          # 3M
                    CodewordCounts([[1, 55]], 15)],         # 3L

                   [CodewordCounts([[4, 9]], 16),           # 4H
                    CodewordCounts([[2, 24]], 26),          # 4Q
                    CodewordCounts([[2, 32]], 18),          # 4M
                    CodewordCounts([[1, 80]], 20)],         # 4L
                   
                   [CodewordCounts([[2, 11], [2, 12]], 22), # 5H
                    CodewordCounts([[2, 15], [2, 16]], 18), # 5Q
                    CodewordCounts([[2, 43]], 24),          # 5M
                    CodewordCounts([[1, 108]], 26)],        # 5L
                   
                   [CodewordCounts([[4, 15]], 28),          # 6H
                    CodewordCounts([[4, 19]], 24),          # 6Q
                    CodewordCounts([[4, 27]], 16),          # 6M
                    CodewordCounts([[2, 68]], 18)]]         # 6L


DATA = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
DATA = "hello this is a test string that i am using"

MODE_BITS = "0100" # byte mode

char_count = f'{len(DATA):08b}' # for byte mode, char_count needs to be 8 bits long (versions 1-9)

# convert the characters to ISO 8859-1 encoding
combined_enc_str = ""
for char in DATA:
    combined_enc_str += f'{ord(char):08b}'

data_bits = MODE_BITS + char_count + combined_enc_str

CW_INFO = -1
VERSION_NUM = -1
EC_LVL = -1

# figure out which version and error correction level we should use
# cw_info[0] == info for ECL H
# cw_info[1] == info for ECL Q
# cw_info[2] == info for ECL M
# cw_info[3] == info for ECL L
for ver_num, cw in enumerate(CODEWORD_BLOCKS):
    
    # unpack the cw array
    h_cw_info, q_cw_info, m_cw_info, l_cw_info = cw
    
    if h_cw_info.getMaxDataBits() >= len(data_bits): # H
        CW_INFO = h_cw_info
        VERSION_NUM = ver_num + 1
        EC_LVL = 2 # Error correction level H == 2
        break
    elif q_cw_info.getMaxDataBits() >= len(data_bits): # Q
        CW_INFO = q_cw_info
        VERSION_NUM = ver_num + 1
        EC_LVL = 3 # Error correction level Q == 3
        break
    elif m_cw_info.getMaxDataBits() >= len(data_bits): # M
        CW_INFO = m_cw_info
        VERSION_NUM = ver_num + 1
        EC_LVL = 0 # Error correction level M == 0
        break
    elif l_cw_info.getMaxDataBits() >= len(data_bits): # L
        CW_INFO = l_cw_info
        VERSION_NUM = ver_num + 1
        EC_LVL = 1 # Error correction level L == 1
        break

if VERSION_NUM == -1:
    print("The data you entered is larger than the largest currently supported QR code version. The current maximum is", int(CODEWORD_BLOCKS[-1][-1].getMaxDataBits()/8)-2, "characters.")
    exit(1)

# add up to 4 zeroes as a terminator, making sure we don't go over the max length
i = 0
while i < 4 and len(data_bits) < CW_INFO.getMaxDataBits():
    data_bits += "0"
    i += 1

# make the length of the bitstring a multiple of 8
while len(data_bits) % 8 != 0:
    data_bits += "0"

# add padding bytes until we reach the required size
while len(data_bits) < CW_INFO.getMaxDataBits():
    data_bits += "1110110000010001"
# if we went over by one byte, remove the extra byte
if len(data_bits) > CW_INFO.getMaxDataBits():
    data_bits = data_bits[:-8]
    
assert len(data_bits) == CW_INFO.getMaxDataBits()

# initialize Galois Field
gf = GaloisField()

# construct the message_ints and eccw_ints arrays
# message_ints/eccw_ints = [group1, group2]
# groupX = [block1, block2, ...]
# blockX = [datacw1, datacw1, ...]
i = 0
message_ints = []
eccw_ints = []
for group_num in range(CW_INFO.getGroupsCount()):
    group = []
    ec_group = []
    for block_num in range(CW_INFO.getBlocksCount(group_num)):
        block = []
        for cw in range(CW_INFO.getDataCWCount(group_num)):
            block.append(int(data_bits[i:i+8], 2))
            i += 8
        group.append(block)
        ec_group.append(calculate_error_correction(block, CW_INFO.getECCWCount(), gf))
    message_ints.append(group)
    eccw_ints.append(ec_group)



# data from messages and error correction codes must be interleaved as following:
# first message int from first block in first group, first message int from second block in first group, first message int from first block in second group, first message int from second block in second group, second message int from first block in first group, etc.
# immediately following the message ints, the error correction codes are interleaved:
# first ec int from first block in first group, first ec int from second block in first group, first ec int from first block in second group, first ec from second block in second group, second ec int from first block in first group, etc.

content_ints = []

# if there are 2 groups, handle their more complicated interleaving 
if CW_INFO.getGroupsCount() > 1:
    i = 0
    j = 0
    
    while i < CW_INFO.getDataCWCount(0) or j < CW_INFO.getDataCWCount(1):
        if i < CW_INFO.getDataCWCount(0):
            for block_num in range(CW_INFO.getBlocksCount(0)):
                content_ints.append(message_ints[0][block_num][i])
            i += 1
            
        if j < CW_INFO.getDataCWCount(1):
            for block_num in range(CW_INFO.getBlocksCount(1)):
                content_ints.append(message_ints[1][block_num][j])
            j += 1

else:
    for cw_num in range(CW_INFO.getDataCWCount(0)): 
        for group_num in range(CW_INFO.getGroupsCount()):
            for block_num in range(CW_INFO.getBlocksCount(group_num)):
                content_ints.append(message_ints[group_num][block_num][cw_num])
                
# interleave the error correction codes, adding them immediately after the message data
for cw_num in range(CW_INFO.getECCWCount()):
    for group_num in range(CW_INFO.getGroupsCount()):
        for block_num in range(CW_INFO.getBlocksCount(group_num)):
            content_ints.append(eccw_ints[group_num][block_num][cw_num])

# convert the list of ints to a bitstring
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

data_list = MovableHeadArray([int(x) for x in list(content_bits)])

module_arr = ModuleArray(pixel_arr, VERSION_NUM, MODULES_PER_EDGE, module_size)

for x in range(MODULES_PER_EDGE-1, 9, -4):
    for y in range(MODULES_PER_EDGE-1, -1, -1):
        if module_arr.update_module(x, y, data_list.get_head()) == 0:
            data_list.inc_head()
        if module_arr.update_module(x-1, y, data_list.get_head()) == 0:
            data_list.inc_head()
    for y in range(0, MODULES_PER_EDGE, 1):
        if module_arr.update_module(x-2, y, data_list.get_head()) == 0:
            data_list.inc_head()
        if module_arr.update_module(x-3, y, data_list.get_head()) == 0:
            data_list.inc_head()
# Add the data bits

# Data bits under the top right finder pattern
# for x in range(MODULES_PER_EDGE-1, MODULES_PER_EDGE-7, -4):
#     for y in range(MODULES_PER_EDGE-1, 8, -1):
#         data_list.curr_index += 1 if module_arr.update_module(x, y, data_list.get_head()) == 0 else 0
#         data_list.curr_index += 1 if module_arr.update_module(x-1, y, data_list.get_head()) == 0 else 0
#     for y in range(9, MODULES_PER_EDGE, 1):
#         data_list.curr_index += 1 if module_arr.update_module(x-2, y, data_list.get_head()) == 0 else 0
#         data_list.curr_index += 1 if module_arr.update_module(x-3, y, data_list.get_head()) == 0 else 0

# Data bits between the left and right finder paterns
# for x in range(MODULES_PER_EDGE-9, 9, -4):
#     for y in range(MODULES_PER_EDGE-1, -1, -1):
#         if y == 6:
#             continue
#         if module_arr.update_module(x, y, data_list.get_head()) == 0:
#             data_list.inc_head()
#         if module_arr.update_module(x-1, y, data_list.get_head()) == 0:
#             data_list.inc_head()
#     for y in range(0, MODULES_PER_EDGE, 1):
#         if y == 6:
#             continue
#         if module_arr.update_module(x-2, y, data_list.get_head()) == 0:
#             data_list.inc_head()
#         if module_arr.update_module(x-3, y, data_list.get_head()) == 0:
#             data_list.inc_head()
        
# Data bits between the top left and bottom left finder paterns
for y in range(MODULES_PER_EDGE-9, 8, -1):
    if module_arr.update_module(8, y, data_list.get_head()) == 0:
        data_list.inc_head()
    if module_arr.update_module(7, y, data_list.get_head()) == 0:
        data_list.inc_head()
for y in range(9, MODULES_PER_EDGE-8, 1):
    if module_arr.update_module(5, y, data_list.get_head()) == 0:
        data_list.inc_head()
    if module_arr.update_module(4, y, data_list.get_head()) == 0:
        data_list.inc_head()
for y in range(MODULES_PER_EDGE-9, 8, -1):
    if module_arr.update_module(3, y, data_list.get_head()) == 0:
        data_list.inc_head()
    if module_arr.update_module(2, y, data_list.get_head()) == 0:
        data_list.inc_head()
for y in range(9, MODULES_PER_EDGE-8, 1):
    if module_arr.update_module(1, y, data_list.get_head()) == 0:
        data_list.inc_head()
    if module_arr.update_module(0, y, data_list.get_head()) == 0:
        data_list.inc_head()

# apply mask
qr_masks = QrMask(MODULES_PER_EDGE, EC_LVL)
qr_image = qr_masks.apply_best_mask(qr_image, module_arr)

trans_ec_lvl = ["M", "L", "H", "Q"]

filename = f"./image-{VERSION_NUM}{trans_ec_lvl[EC_LVL]}.png"

try:
    qr_image.save(filename)
except Exception as e:
    print("Error saving file:", e)
else:
    pass
    print(f"Output saved as {filename}")



# TODO: if version > 7, we have to include the version number (https://www.thonky.com/qr-code-tutorial/format-version-information#version-information)