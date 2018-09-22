import subprocess
import os 

def convert_to_autovot_wav(input_file, output_file):
        '''Takes a filename and returns an output wav with the correct
        params for autovot'''
        par_dir = os.path.dirname(output_file)
        if not os.path.exists(par_dir):
            os.makedirs(par_dir)
        subprocess.run(['sox', input_file, '-c', '1', '-r', '16000', output_file])

