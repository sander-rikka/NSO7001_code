import os


def delete_raw_files(path):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        os.remove(file_path)


if __name__ == '__main__':
    # add paths as necessary
    paths_to_delete = ['data/radar_unzipped', 'data/radar_raw']

    for path in paths_to_delete:
        delete_raw_files(path)
