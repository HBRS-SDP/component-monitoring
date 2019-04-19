from os import listdir
from os.path import join, isfile

class ConfigUtils(object):
    @staticmethod
    def get_file_names_in_dir(dir_name):
        '''Returns a list file names in the given directory.

        Keyword arguments:
        dir_name: str -- directory name

        '''
        file_names = list()
        for f_name in listdir(dir_name):
            f_path = join(dir_name, f_name)
            if isfile(f_path):
                file_names.append(f_name)
        return file_names
