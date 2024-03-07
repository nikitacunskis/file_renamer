import os
import json
import re
import logging
from datetime import datetime
from moviepy.editor import VideoFileClip

# Configure logging
log_filename = 'directory_reader.log'
logging.basicConfig(filename=log_filename, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class ConfigReader:
    def __init__(self, config_file):
        self.config_file = config_file

    def get_config(self):
        print("Reading configuration...")
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                print("Configuration successfully read.")
                return config
        except FileNotFoundError:
            msg = "Configuration file not found."
            print(msg)
            logging.error(msg)
        except json.JSONDecodeError:
            msg = "Error decoding JSON from the configuration file."
            print(msg)
            logging.error(msg)
        except Exception as e:
            msg = f"An unexpected error occurred: {e}"
            print(msg)
            logging.error(msg)
        return {}


class DirectoryReader:
    def __init__(self, config_reader):
        self.config_reader = config_reader
        self.config = self.config_reader.get_config()
        self.folder_path = self.config.get('folder_path', '')
        self.large_file_marker = self.config.get('large_file_marker', 0)
        self.filename_template = self.config.get(
            'filename_template', '{date}_{size_marker}_{number}_{length_seconds}')
        msg = f"Directory reader initialized with folder_path: {self.folder_path}"
        print(msg)
        logging.info(msg)

    def list_files(self):
        print("Listing files in directory...")
        files_info = []
        try:
            for filename in os.listdir(self.folder_path):
                if filename.endswith('.mp4'):
                    print(f"Processing file: {filename}")
                    path = os.path.join(self.folder_path, filename)
                    if os.path.isfile(path):
                        number_match = re.search(r'_([0-9]+)\.mp4$', filename)
                        if number_match:
                            number = number_match.group(1)
                            length_seconds = self.read_video_length(path)
                            files_info.append({
                                'filename': filename,
                                'number': number,
                                'length_seconds': length_seconds,
                                'date': datetime.now().strftime('%Y%m%d'),
                                'size_marker': 'L' if length_seconds > self.large_file_marker else 'S'
                            })
        except Exception as e:
            msg = f"An error occurred while listing files: {e}"
            print(msg)
            logging.error(msg)
        print("Finished listing files.")
        return files_info

    def read_video_length(self, file_path):
        print(f"Reading video length for: {file_path}")
        try:
            with VideoFileClip(file_path) as video:
                duration = round(video.duration)
                print(f"Video length: {duration} seconds.")
                return duration

        except Exception as e:
            msg = f"Error reading video length: {e}"
            print(msg)
            logging.error(msg)
            return 0

    def generate_new_filenames(self):
        print("Generating new filenames...")
        files_info = self.list_files()
        files_info.sort(key=lambda x: int(x['number']))
        new_filenames_info = []
        numbers_seen = {}
        duplicates = set()
        all_numbers = []

        for file_info in files_info:
            number = int(file_info['number'])
            all_numbers.append(number)
            if number in numbers_seen:
                duplicates.add(number)
                msg = f"Warning: Duplicate number detected for {number}. Ignoring files: {numbers_seen[number]}, {file_info['filename']}"
                print(msg)
                logging.warning(msg)
            else:
                numbers_seen[number] = file_info['filename']

        all_numbers = sorted(list(set(all_numbers)))
        if all_numbers and all_numbers[0] == 0:
            user_input = input(
                "The first number is 0. Do you want to adjust all numbers by incrementing them by 1? (yes/no): ")
            if user_input.strip().lower() == 'yes':
                all_numbers = [x + 1 for x in all_numbers]
                numbers_seen = {k + 1: v for k, v in numbers_seen.items()}
        missing_numbers = [x for x in range(all_numbers[0], all_numbers[-1] + 1) if x not in all_numbers]

        if missing_numbers:
            missing_numbers_str = ", ".join(map(str, missing_numbers))
            msg = f"Missing numbers detected: {missing_numbers_str}."
            print(msg)
            logging.info(msg)

        for file_info in files_info:
            if file_info['number'] not in duplicates:
                adjusted_number = int(file_info['number']) + 1 if all_numbers[0] == 1 else int(file_info['number'])
                new_filename = self.filename_template.format(
                    date=file_info['date'],
                    size_marker=file_info['size_marker'],
                    number=str(adjusted_number).zfill(6),
                    length_seconds=str(file_info['length_seconds']).zfill(3)
                ) + ".mp4"
                new_filenames_info.append(
                    (file_info, file_info['filename'], new_filename))
        print("New filenames generated.")

        return new_filenames_info

    def rename_files(self):
        new_filenames = self.generate_new_filenames()

        print("Proposed file renames (excluding duplicates):")
        for _, old_filename, new_filename in new_filenames:
            msg = f"{old_filename} -> {new_filename}"
            print(msg)

        user_response = input("Do you want to rename the files? (yes/no): ")
        if user_response.lower() in ['yes', 'y']:
            for _, old_filename, new_filename in new_filenames:
                print(f"Renaming {old_filename} to {new_filename}...")
                old_path = os.path.join(self.folder_path, old_filename)
                new_path = os.path.join(self.folder_path, new_filename)
                try:
                    os.rename(old_path, new_path)
                    msg = f"Renamed {old_filename} to {new_filename}"
                    print(msg)
                    logging.info(msg)
                except Exception as e:
                    msg = f"Error renaming {old_filename} to {new_filename}: {e}"
                    print(msg)
                    logging.error(msg)
            print("File renaming completed.")
        else:
            print("File renaming cancelled.")


# Main execution
if __name__ == "__main__":
    config_file = 'config.json'
    config_reader = ConfigReader(config_file)
    directory_reader = DirectoryReader(config_reader)
    directory_reader.rename_files()