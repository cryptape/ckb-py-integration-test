import os
import platform
import requests
import tarfile
import zipfile
from tqdm import tqdm

versions = ['0.109.0','0.110.0','0.111.0-rc6']  # Replace with your versions
DOWNLOAD_DIR = "download"
SYSTEMS = {
    'Windows': {
        'url': 'https://github.com/nervosnetwork/ckb/releases/download/v{version}/ckb_v{'
               'version}_x86_64-pc-windows-gnu.zip',
        'ext': '.zip',
    },
    'Linux': {
        'x86_64': {
            'url': 'https://github.com/nervosnetwork/ckb/releases/download/v{version}/ckb_v{'
                   'version}_x86_64-unknown-linux-gnu.tar.gz',
            'ext': '.tar.gz',
        },
        'aarch64': {
            'url': 'https://github.com/nervosnetwork/ckb/releases/download/v{version}/ckb_v{'
                   'version}_aarch64-unknown-linux-gnu.tar.gz',
            'ext': '.tar.gz',
        },
    },
    'Darwin': {
        'x86_64': {
            'url': 'https://github.com/nervosnetwork/ckb/releases/download/v{version}/ckb_v{'
                   'version}_aarch64-apple-darwin-portable.zip',
            'ext': '.zip',
        },
        'arm64': {
            'url': 'https://github.com/nervosnetwork/ckb/releases/download/v{version}/ckb_v{'
                   'version}_aarch64-apple-darwin-portable.zip',
            'ext': '.zip',
        },
    },
}


def download_file(url, filename):
    """
    Download a file from the specified URL and save it locally.

    Args:
        url (str): The URL of the file to download.
        filename (str): The name to save the downloaded file as.

    Raises:
        requests.HTTPError: If an HTTP error occurs during the download.

    """
    print("Downloading URL: {url}".format(url=url))
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    t = tqdm(total=total_size, unit='iB', unit_scale=True)

    with open(filename, 'wb') as f:
        for data in response.iter_content(block_size):
            t.update(len(data))
            f.write(data)
    t.close()

    if total_size != 0 and t.n != total_size:
        raise Exception("ERROR: Something went wrong during the download.")


def extract_file(filename, path):
    temp_path = os.path.join(path, 'temp')
    os.makedirs(temp_path, exist_ok=True)

    if filename.endswith('.zip'):
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(temp_path)
    elif filename.endswith('.tar.gz'):
        with tarfile.open(filename, 'r:gz') as tar_ref:
            tar_ref.extractall(temp_path)

    # Move the extracted files from the subdirectory to the target directory
    extracted_subdir = os.path.join(temp_path, os.listdir(temp_path)[0])
    for file in os.listdir(extracted_subdir):
        os.rename(os.path.join(extracted_subdir, file), os.path.join(path, file))

    # Remove the downloaded zip or tar.gz file and the temporary directory
    os.remove(filename)
    os.rmdir(extracted_subdir)
    os.rmdir(temp_path)

    # Change permission of ckb and ckb-cli files
    for file in ['ckb', 'ckb-cli']:
        filepath = os.path.join(path, file)
        if os.path.isfile(filepath):
            os.chmod(filepath, 0o755)


def download_ckb(ckb_version):
    system = platform.system()
    architecture = platform.machine() if system in ['Linux', 'Darwin'] else ''
    print(f"system:{system},architecture:{architecture}"
          .format(system=system, architecture=architecture))
    url = SYSTEMS[system][architecture]['url'].format(version=ckb_version)
    ext = SYSTEMS[system][architecture]['ext']

    filename = f'ckb_v{ckb_version}_binary{ext}'
    download_path = os.path.join(DOWNLOAD_DIR, ckb_version).split("-")[0]
    os.makedirs(download_path, exist_ok=True)

    download_file(url, filename)
    extract_file(filename, download_path)


for version in versions:
    download_ckb(version)
