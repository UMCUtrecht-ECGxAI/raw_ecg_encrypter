import argparse
from cryptography.fernet import Fernet
import xml.etree.ElementTree as ET
import pydicom as dicom
from pydicom import errors
import os
import pandas as pd
from helpers import *
import hashlib
from tqdm import tqdm

def write_password(filename):
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(filename, "wb") as key_file:
        key_file.write(key)

def load_password(filename):
    """
    Loads the key from the current directory named `key.key`
    """
    return open(filename, "rb").read()

def encrypt(filename_input, filename_output, key):
    """
    Given a filename (str) and key (bytes), it encrypts the file and write it
    """
    f = Fernet(key)
    with open(filename_input, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # write the encrypted file
    with open(filename_output, "wb") as file:
        file.write(encrypted_data)

def remove_specific_xml_field(xml_root, field_path):
    """
    Removes XML field at the specified path in the XML. Works for top-level and
    nested fields.
    """
    if xml_root.find(field_path) is not None:
        if len(field_path.split('/')) > 1:
            root_path = field_path.split('/')[0]
            xml_root.find(root_path).remove(xml_root.find(field_path))
        else:
            xml_root.remove(xml_root.find(field_path))
            
    return xml_root

def run(config):
    """
    Main loop for pseudonymizing and encrypting all the files.
    """    
    
    dir_list = []
    
    print('Reading folder...')

    if config.manufacturer == 'DICOMDIR':  # In case of structured DICOMDIR director(y)(ies)
            dicomdir_list = []
            for root, subdirs, files in os.walk(config.in_folder):
                for file in files:
                    if file.startswith('DICOMDIR'):
                        dicomdir_list.append(os.path.join(root, file))

            for dicom_dir_file in dicomdir_list:
                dicom_dir = dicom.filereader.read_dicomdir(dicom_dir_file)
                base_dir = os.path.dirname(dicom_dir_file)

                for patient_record in dicom_dir.patient_records:
                    for study in patient_record.children:
                        for series in study.children:
                            image_records = series.children
                            image_filenames = [os.path.join(base_dir, *image_rec.ReferencedFileID)
                                            for image_rec in image_records]
                            for item in image_filenames:
                                dir_list.append(item)
    
    else: 
        for root, subdirs, files in tqdm(os.walk(config.in_folder)):
            for file in files:
                if (file.endswith('.xml') or file.endswith('.XML')):
                    dir_list.append(os.path.join(root, file))
                elif (file.startswith('1.2.840.113654.2.70.1') or 
                    file.endswith('.dcm') or file.endswith('.DCM')):
                    ds = dicom.read_file(os.path.join(root, file))
                    if ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.9.1.1':
                        dir_list.append(os.path.join(root, file))

    print(f'{str(len(dir_list))} files found in this folder, is that correct?')

    keys = pd.read_csv(config.key, sep=None, engine='python', encoding='utf-8-sig')
    if keys['PID'].dtypes == int or keys['PID'].dtypes == float:
        print('Adding leading zeros to numeric PatientID, is that correct?')
        keys['PID'] = keys['PID'].astype(int).astype(str).apply('{:0>7}'.format)
    else:
        keys['PID'] = keys['PID'].astype(str)
    keys['PseudoID'] = keys['PseudoID'].astype(str)

    if not os.path.exists(os.path.join(config.in_folder, 'password.key')):
        print('Generating new password...')
        write_password(os.path.join(config.in_folder, 'password.key'))
    else:
        print('Using current password...')

    password = load_password(os.path.join(config.in_folder, 'password.key'))
    
    print('Starting pseudonymisation and encryption...')

    for idx, path in tqdm(enumerate(dir_list)):    
        if config.manufacturer == 'MUSE':
            xml_tree = ET.parse(path)
            xml_root = xml_tree.getroot()

            # Get required variables from XML file
            xml_dict = make_dict_from_tree(xml_root)['RestingECG']
            patient_id = str(xml_dict['PatientDemographics']['PatientID'])
            acq_date = xml_dict['TestDemographics']['AcquisitionDate']
            acq_time = xml_dict['TestDemographics']['AcquisitionTime']
            timestamp = acq_date + acq_time

            # Remove specific fields
            remove_field = ['PatientDemographics', 'Order', 
                'TestDemographics/OverreaderID', 
                'TestDemographics/EditorID', 
                'TestDemographics/OverreaderLastName', 
                'TestDemographics/OverreaderFirstName', 
                'TestDemographics/EditorLastName', 
                'TestDemographics/EditorFirstName', 
                'TestDemographics/SecondaryID'
            ]

            for field_path in remove_field:
                xml_root = remove_specific_xml_field(xml_root, field_path)

        elif config.manufacturer == 'MORTARA':
            xml_tree = ET.parse(path)
            xml_root = xml_tree.getroot()

            # Get required variables from XML file
            patient_id = str(xml_root.find('./SUBJECT').attrib['ID'])
            timestamp = xml_root.find('.').attrib['ACQUISITION_TIME_XML']

            # Remove specific fields
            remove_field = [
                'DEMOGRAPHIC_FIELDS',
                'SUBJECT',
                'SITE'
            ]

            for field_path in remove_field:
                xml_root = remove_specific_xml_field(xml_root, field_path)

        elif config.manufacturer == 'DICOM' or config.manufacturer == 'DICOMDIR':
            ds = dicom.read_file(path)

            # Get required variables from DICOM file
            patient_id = str(ds.PatientID)
            try:
                timestamp = ds.StudyDate + ds.StudyTime
            except Exception as e:
                print(e)
                print(path)

            if 'PatientIdentityRemoved' not in ds or ds.PatientIdentityRemoved == 'NO':
                # Remove PatientDemograpics
                ds.PatientName = ''
                ds.PatientID = ''
                ds.PatientBirthDate = ''          

        # Define new filename
        if patient_id in keys['PID'].values:
            pseudo_id = keys.loc[keys['PID'] == patient_id, 'PseudoID'].values[0]
        else:
            print(f'The XML/DCM file with name {path} has no associated RedCap ID, please check.')
            print(patient_id)
            print(keys['PID'])
            continue
        
        timestamp_hash = hashlib.sha256(timestamp.encode('utf-8')).hexdigest()[-10:]
        file_out = str(pseudo_id) + '_' + timestamp_hash

        # Save pseudonimized and encrypted files
        if config.manufacturer in ['MUSE', 'MORTARA']:
            xml_tree.write(os.path.join(config.out_folder, file_out + '.xml'))
            encrypt(os.path.join(config.out_folder, file_out + '.xml'), 
            os.path.join(config.encrypted_folder, file_out + '.enc'), password)
        elif config.manufacturer in ['DICOM', 'DICOMDIR']:
            ds.save_as(os.path.join(config.out_folder, file_out + '.dcm'))
            encrypt(os.path.join(config.out_folder, file_out + '.dcm'), 
            os.path.join(config.encrypted_folder, file_out + '.enc'), password)
    
    print(f'Done, processed {str(idx+1)} files!')

    return idx+1

if __name__ == "__main__":
    # Parser
    parser = argparse.ArgumentParser()

    parser.add_argument('--in_folder', type=str, default="test_dir", help="Path to folder with xml or dicom waveform files")
    parser.add_argument('--out_folder', type=str, default="out_test_dir", help="Folder name to put converted files in")
    parser.add_argument('--encrypted_folder', type=str, default="encrypt_test_dir", help="Folder name to put encrypted files in")
    parser.add_argument('--key', type=str, default="key.csv", help="CSV file with local PIDs (named 'PID') and pseudonyms (named 'PseudoID')")
    parser.add_argument('--manufacturer', type=str, default="MUSE", help="Enter manufacturer, options: MUSE or MORTARA or DICOM or DICOMDIR")
    
    config = parser.parse_args()

    assert(config.manufacturer in ['MUSE', 'MORTARA', 'DICOM', 'DICOMDIR'])

    run(config)
