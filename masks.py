import numpy

class QrMask:
    
    def __init__(self, modules_per_edge, err_corr_lvl):
        self.modules_per_edge = modules_per_edge
        self.err_corr_lvl = err_corr_lvl


    def mask_num_0(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if (row + column) % 2 == 0:
            return not module_val
        else:
            return module_val

    def mask_num_1(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if row % 2 == 0:
            return not module_val
        else:
            return module_val

    def mask_num_2(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if column % 3 == 0:
            return not module_val
        else:
            return module_val

    def mask_num_3(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if (row + column) % 3 == 0:
            return not module_val
        else:
            return module_val

    def mask_num_4(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if (numpy.floor(row/2) + numpy.floor(column/3)) % 2 == 0:
            return not module_val
        else:
            return module_val

    def mask_num_5(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if ((row * column) % 2) + ((row * column) % 3) == 0:
            return not module_val
        else:
            return module_val

    def mask_num_6(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if (((row * column) % 2) + ((row * column) % 3)) % 2 == 0:
            return not module_val
        else:
            return module_val

    def mask_num_7(self, module_arr, column, row):
        module_val = module_arr.get_module(column, row)
        if (((row + column) % 2) + ((row * column) % 3)) % 2 == 0:
            return not module_val
        else:
            return module_val



    def apply_mask(self, module_arr, mask_func):
        # Data bits under the top right finder pattern
        for x in range(self.modules_per_edge-8, self.modules_per_edge, 1):
            for y in range(9, self.modules_per_edge, 1):
                module_arr.update_module(x, y, mask_func(module_arr, x, y))
                
        # Data bits between the left and right finder paterns
        for x in range(9, self.modules_per_edge-8, 1):
            for y in range(0, self.modules_per_edge, 1):
                if y == 6:
                    continue
                module_arr.update_module(x, y, mask_func(module_arr, x, y))
                
        # Data bits between the top left and bottom left finder paterns
        for y in range(9, self.modules_per_edge-8, 1):
            module_arr.update_module(8, y, mask_func(module_arr, 8, y))
            module_arr.update_module(7, y, mask_func(module_arr, 7, y))
        for x in range(0, 6, 1):
            for y in range(9, self.modules_per_edge-8, 1):
                module_arr.update_module(x, y, mask_func(module_arr, x, y))



    def eval_condition_1(self, module_arr):
        # Evaluation Condition #1: 5+ same-colored modules in a row/column
        penalty = 0
        prev_column = [-1] * self.modules_per_edge
        consecutive_count_column = [1] * self.modules_per_edge
        
        for x in range(0, self.modules_per_edge):
            consecutive_count = 1
            prev_module = -1

            for y in range(0, self.modules_per_edge):
                curr_module = module_arr.get_module(x, y)
                
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

    def eval_condition_2(self, module_arr):
        # Evaluation Condition #2: 2x2 squares of the same color
        penalty = 0
        for x in range(0, self.modules_per_edge-1):
            for y in range(0, self.modules_per_edge-1):
                if module_arr.get_module(x, y) == module_arr.get_module(x+1, y) == module_arr.get_module(x, y+1) == module_arr.get_module(x+1, y+1):
                    penalty += 3

        return penalty

    def eval_condition_3(self, module_arr):
        # Evaluation Condition #3: patterns of dark-light-dark-dark-dark-light-dark with 4 light on either side
        patt_1 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
        patt_2 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
        patt_len = len(patt_1)
        
        penalty = 0
        for x in range(0, self.modules_per_edge-9):
            for y in range(0, self.modules_per_edge-9):
                test_list_vert = []
                test_list_horz = []
                for i in range(patt_len):
                    test_list_vert.append(module_arr.get_module(x, y+i))
                    test_list_horz.append(module_arr.get_module(x+i, y))
                if test_list_vert == patt_1 or test_list_vert == patt_2:
                    penalty += 40
                if test_list_horz == patt_1 or test_list_horz == patt_2:
                    penalty += 40

        return penalty

    def eval_condition_4(self, module_arr):
        # Evaluation Condition #4: ratio of black to white modules 
        dark_count = 0
        total_module_count = self.modules_per_edge * self.modules_per_edge
        for x in range(0, self.modules_per_edge):
            for y in range(0, self.modules_per_edge):
                if module_arr.get_module(x, y) == 1:
                    dark_count += 1

        dark_percent = (dark_count/total_module_count) * 100
        distance_from_equal = int(abs(dark_percent - 50))
        
        mult = 0
        while (distance_from_equal-1) > mult:
            mult += 1

        return mult * 10

    def calc_mask_score(self, module_arr):
        penalty = self.eval_condition_1(module_arr)
        penalty += self.eval_condition_2(module_arr)
        penalty += self.eval_condition_3(module_arr)
        penalty += self.eval_condition_4(module_arr)
        return penalty



    def add_format_bits(self, module_arr, mask_ver):
        ec_lvl_bits = f'{self.err_corr_lvl:02b}'
        mask_ver_bits = f'{mask_ver:03b}'
        format_bits = ec_lvl_bits + mask_ver_bits
        parity_bits = format_bits
        gen_poly_int = 0b10100110111
        mask = 0b100000000000000
        ten_mask_max = 0b111110000000000
        
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
        
        # QR code specification says to XOR the format bits with 101010000010010
        format_bits = f'{(0b101010000010010 ^ int(format_bits, 2)):015b}'
        assert len(format_bits) == 15
        
        # add the format bits to the QR code
        format_list = [int(i) for i in list(format_bits)]
        
        # format bits to the right of the bottom-left finder pattern
        for y in range(self.modules_per_edge-1, self.modules_per_edge-8, -1):
            module_arr.update_module(8, y, format_list.pop(0), True)
        
        # format bits to the right of the top-left finder pattern
        for y in range(8, -1, -1):
            if y == 6: continue
            module_arr.update_module(8, y, format_list.pop(0), True)

        format_list = [int(i) for i in list(format_bits)]
        
        # format bits under the top left finder pattern
        for x in range(0, 6, 1):
            module_arr.update_module(x, 8, format_list.pop(0), True)
        module_arr.update_module(7, 8, format_list.pop(0), True)
        
        # format bits under the top right finder pattern
        for x in range(self.modules_per_edge-8, self.modules_per_edge, 1):
            module_arr.update_module(x, 8, format_list.pop(0), True)

    
    
    def apply_best_mask(self, qr_image, module_arr):
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
        module_arr.set_pixel_arr(qr_image_mask_0.load())
        self.apply_mask(module_arr, self.mask_num_0)
        self.add_format_bits(module_arr, 0)
        min_mask_score = self.calc_mask_score(module_arr)
        qr_image = qr_image_mask_0

        # mask 1
        module_arr.set_pixel_arr(qr_image_mask_1.load())
        self.apply_mask(module_arr, self.mask_num_1)
        self.add_format_bits(module_arr, 1)
        mask_score = self.calc_mask_score(module_arr)
        if mask_score < min_mask_score:
            min_mask_score = mask_score
            qr_image = qr_image_mask_1

        # mask 2
        module_arr.set_pixel_arr(qr_image_mask_2.load())
        self.apply_mask(module_arr, self.mask_num_2)
        self.add_format_bits(module_arr, 2)
        mask_score = self.calc_mask_score(module_arr)
        if mask_score < min_mask_score:
            min_mask_score = mask_score
            qr_image = qr_image_mask_2

        # mask 3
        module_arr.set_pixel_arr(qr_image_mask_3.load())
        self.apply_mask(module_arr, self.mask_num_3)
        self.add_format_bits(module_arr, 3)
        mask_score = self.calc_mask_score(module_arr)
        if mask_score < min_mask_score:
            min_mask_score = mask_score
            qr_image = qr_image_mask_3

        # mask 4
        module_arr.set_pixel_arr(qr_image_mask_4.load())
        self.apply_mask(module_arr, self.mask_num_4)
        self.add_format_bits(module_arr, 4)
        mask_score = self.calc_mask_score(module_arr)
        if mask_score < min_mask_score:
            min_mask_score = mask_score
            qr_image = qr_image_mask_4

        # mask 5
        module_arr.set_pixel_arr(qr_image_mask_5.load())
        self.apply_mask(module_arr, self.mask_num_5)
        self.add_format_bits(module_arr, 5)
        mask_score = self.calc_mask_score(module_arr)
        if mask_score < min_mask_score:
            min_mask_score = mask_score
            qr_image = qr_image_mask_5

        # mask 6
        module_arr.set_pixel_arr(qr_image_mask_6.load())
        self.apply_mask(module_arr, self.mask_num_6)
        self.add_format_bits(module_arr, 6)
        mask_score = self.calc_mask_score(module_arr)
        if mask_score < min_mask_score:
            min_mask_score = mask_score
            qr_image = qr_image_mask_6

        # mask 7
        module_arr.set_pixel_arr(qr_image_mask_7.load())
        self.apply_mask(module_arr, self.mask_num_7)
        self.add_format_bits(module_arr, 7)
        mask_score = self.calc_mask_score(module_arr)
        if mask_score < min_mask_score:
            min_mask_score = mask_score
            qr_image = qr_image_mask_7
        
        return qr_image