# Manual for the ecg_encrypter
Python script to automatically remove patient information from all sorts of raw ECG files. It automatically replaces the patient ID in the files with a pseudonymized ID that you provide, and deletes all other sensitive information. In a second step the ECGs are encrypted using AES128 encryption in CBC mode with a SHA256 HMAC message authentication code. These files can be safely shared between centers.

1. Install Anaconda/Miniconda on your system.

2. Open Terminal (on Mac) or Anaconda Prompt (on Windows).

3.  Navigate to the folder where you put the tool using `cd` and the path.

4. Install the following packages: cryptography, pandas, tqdm and pydicom:

    ```
    conda install -c conda-forge pandas cryptography tqdm pydicom
    ```

5. Optional: test if your installation is working by running the following command:
    ```
    pytest
    ```

6. Place all XML/DCM files in the same folder and create two other empty folders (one for pseudonymised ECGs, one for encrypted ECGs). Files may be in one of the subfolders. They are a few options how the input folder can be organized:
    * For MUSE and MORTARA systems: files can be in the parent or subfolders and should end with `.xml` or `.XML`. For manufacturer select **MUSE** or **MORTARA**, where appropriate.
    * For DICOM systems there are two options:
        * Files are in the parent or subfolders and end with `.dcm` or `.DCM` or start with `1.2.840.113654.2.70.1`. As these type of files can both be a real waveform DICOM or an encapsulated PDF, we will check if the UID is 1.2.840.10008.5.1.4.1.1.9.1.1. For manufacturer select **DICOM**.
        * Files are in a DICOMDIR folder structure. For manufacturer select **DICOMDIR**.

7. Create a CSV file, semicolon-delimited, with in one column named `PID` the patient IDs as used in the XML/DCM file and in one column named `PseudoID` the PseudoIDs (please see example files and folders in the repository).

8. Run the encrypter with the following command in the terminal or Anaconda Prompt (don't forget to replace `in_test_dir`, `out_test_dir`, `excrypt_test_dir` and `test_key.csv` with the correct full paths, like `C:\Users\Test\in_test_dir` etc). Please enter the correct manufacturerer too.

    ```
    python ecg_encrypter.py --in_folder in_test_dir_xml --out_folder out_test_dir --encrypted_folder encrypt_test_dir --key test_key.csv --manufacturer MUSE
    python ecg_encrypter.py --in_folder in_test_dir_dcm --out_folder out_test_dir --encrypted_folder encrypt_test_dir --key test_key.csv --manufacturer DICOM
    ```

9. Make sure that all files are processed, the script will let you know how many files will be processed.

10. IMPORTANT: the script generates a password in the `in_folder`, when it does not exist yet. Make sure to save this password somewhere, otherwise decryption won't be possible.

11. Upload the encrypted files to SurfDrive, share the password file (in the in_folder) via another channel (such as email).