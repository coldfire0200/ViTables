from PyQt5.QtCore import QFileInfo
import numpy, ast

def load_raw_bin(dir_name, file_name, dtype = numpy.single, complex = False):
    if file_name.endswith('.txt'):
        txt_file = file_name
        bin_file = file_name[:-3] + 'bin'
    elif file_name.endswith('.bin'):
        txt_file = file_name[:-3] + 'txt' if file_name.endswith('.bin') else (file_name + '.txt')
        bin_file = file_name
    else:
        txt_file = file_name + '.txt'
        bin_file = file_name + '.bin'
    if not QFileInfo(dir_name + '/' + txt_file).exists():
        print(f'<err>file does not exist: {dir_name + "/" + txt_file}')
        return False, None
    # load txt file (shape)
    with open(dir_name + '/' + txt_file) as read_file:
        shape = [ast.literal_eval(line.strip()) for line in read_file if line.strip()]
        data = numpy.fromfile(dir_name + '/' + bin_file, dtype = dtype)
        if complex:
            data = data[::2] + 1.0j * data[1::2]
        else:
            type_per_sample = len(data) // numpy.prod(shape)
            if type_per_sample > 1:
                shape = [type_per_sample] + shape
        data = numpy.squeeze(data.reshape(list(reversed(shape))))
    return True, data

def save_raw_bin(dir_name, file_name, data: numpy.ndarray):
    # save bin file
    data.tofile(dir_name + '/' + file_name + '.bin')
    # save dim file
    with open(dir_name + '/' + file_name + '.txt', 'w') as write_file:
        for dim in reversed(data.shape):
            write_file.write(f'{dim}\n')