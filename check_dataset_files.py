import argparse
import os
import pathlib
from functools import partial
import multiprocessing
import shutil
import time

import tensorflow as tf
from tqdm import tqdm

num_files = 0
cur_file = 0

def main():
    # Define the command line arguments
    parser = argparse.ArgumentParser(description='Check a path containing the dataset files for valid files')
    parser.add_argument('dir', type=str, help='Parent directory containing the dataset files')
    parser.add_argument('--out', type=str, required=False, help='directory to keep invalid files')
    
    # Parse the command line arguments
    args = parser.parse_args()
    # Check if the list of invalid files already exists
    invalid_file_path = os.path.join(args.dir, 'invalid_files.txt')
    if os.path.exists(invalid_file_path):
        print(f'Found list of invalid files at {invalid_file_path}')
        with open(invalid_file_path, 'r') as f:
            invalid_files = f.read().splitlines()
    else:
        print(f'Checking files in {args.dir} for validity')
        file_list = find_files(args.dir)
        print(f'Found {len(file_list)} total files')
        global num_files
        num_files = len(file_list)
        
        # Create shared counter
        manager = multiprocessing.Manager()
        counter = manager.Value('i', 0)
        
        # Split file_list into chunks
        num_processes = multiprocessing.cpu_count()
        chunk_size = len(file_list) // num_processes
        file_chunks = [file_list[i:i+chunk_size] for i in range(0, len(file_list), chunk_size)]
        
        # Use multiprocessing.Pool.map to check each chunk in parallel
        pool = multiprocessing.Pool(num_processes)
        results = pool.starmap_async(find_invalid, [(chunk, counter) for chunk in file_chunks])
        # Show progress bar while waiting for results
        pbar = tqdm(total=len(file_list))
        while not results.ready():
            # Update progress bar with current value of the shared counter
            pbar.update(counter.value - pbar.n)
            time.sleep(1)
        pbar.update(counter.value - pbar.n)
        pbar.close()
        # Get invalid files from results
        invalid_files = []
        for result in results.get():
            invalid_files.extend(result)
        pool.close()
        pool.join()
        
        # Flatten the list of invalid files
        # invalid_files = [file for sublist in invalid_files for file in sublist]
        print(f'Found {len(invalid_files)} invalid files out of {len(file_list)} files')
        
        # Write the list of invalid files to a file
        with open(invalid_file_path, 'w') as f:
            f.write('\n'.join(invalid_files))
    
    if input('Move invalid files to .invalid directory? (y/n) ') == 'y':
        move_files(invalid_files, args.dir, args.out)
    print('Done')

def move_files(file_list, src, dest_root=None):
    for file in file_list:
        if dest_root is None:
            invalid_dir = os.path.normpath(os.path.join(src, '.invalid'))
        else:
            invalid_dir = os.path.normpath(dest_root)
        try:
            if not os.path.exists(invalid_dir):
                os.mkdir(invalid_dir)
        except:
            print(f'Unable to create directory {invalid_dir}')
            continue
        else:
            try:
                dest = os.path.normpath(os.path.join(invalid_dir, os.path.relpath(file, start=src)))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(os.path.normpath(file), dest)
            except:
                print(f'Unable to move file {file} to {invalid_dir}')
                continue

def find_invalid(file_list, counter) -> list:
    invalid_files = []
    for file in file_list:
        with tf.io.gfile.GFile(file, 'r') as tf_file:
            try:
                tf_file.read()
            except:
                invalid_files.append(os.path.normpath(file))
                # Check if there is a corresponding file with the opposite extension
                file_name, file_ext = os.path.splitext(file)
                opposite_ext = '' if file_ext == '.json' else '.json'
                opposite_file = file_name + opposite_ext
                if os.path.exists(opposite_file):
                    invalid_files.append(os.path.normpath(opposite_file))
        counter.value += 1
    return invalid_files

## Get a list of files from path
def find_files(path):
    files = []
    with os.scandir(path) as entries:
        for entry in entries:
            #  (pathlib.Path(entry.path).suffix not in ['.jpg','.jpeg','.png','.nfo'])
            if entry.is_file():
                # Add the file path to the list if the entry is a file
                files.append(os.path.normpath(entry.path))
            elif entry.is_dir():
                # Recursively search for files in the subdirectory if the entry is a directory
                files.extend(find_files(entry.path))
    return files
if __name__ == '__main__':
    main()