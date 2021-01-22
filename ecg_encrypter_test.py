import pytest
import argparse
from ecg_encrypter import run

def parse(input_folder, manufacturer):
    parser = argparse.ArgumentParser()

    parser.add_argument('--in_folder', type=str, default="test_dir", help="Path to folder with xml or dicom waveform files")
    parser.add_argument('--out_folder', type=str, default="out_test_dir", help="Folder name to put converted files in")
    parser.add_argument('--encrypted_folder', type=str, default="encrypt_test_dir", help="Folder name to put encrypted files in")
    parser.add_argument('--key', type=str, default="key.csv", help="CSV file with local PIDs (named 'PID') and pseudonyms (named 'PseudoID')")
    parser.add_argument('--manufacturer', type=str, default="MUSE", help="Enter manufacturer, options: MUSE or MORTARA or DICOM or DICOMDIR")

    config = parser.parse_args([
        '--in_folder', input_folder,
        '--out_folder', 'out_test_dir',
        '--encrypted_folder', 'encrypt_test_dir',
        '--key', 'test_key.csv',
        '--manufacturer', manufacturer
    ])

    return config

def run_with_testfiles_xml():
    config = parse('in_test_dir_xml', 'MUSE')

    no_of_files = run(config)

    return no_of_files

def test_run_with_testfiles():
    assert run_with_testfiles_xml() == 2

def run_with_testfiles_dcm():
    config = parse('in_test_dir_dcm', 'DICOM')

    no_of_files = run(config)

    return no_of_files

def test_run_with_testfiles_dcm():
    assert run_with_testfiles_dcm() == 2