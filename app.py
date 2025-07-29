import streamlit as st
import os
import subprocess
import tempfile
from pathlib import Path
import shutil
import zipfile
import re

# --- Configuration for Base Directory ---
BASE_TESTING_DIR = Path("C:/Users/lakebridge/Lakebridge-Testing-Files")

# Title
st.image("assets/tiger_icon.png", width=100)
st.title("🧠 Tiger CodeAnalyzer")

# Input source section
st.subheader("📂 Provide Input Source Code")

upload_option = st.radio("Choose input method:", ["Upload Files", "Upload Folder (Zip)"])

uploaded_files = None
zip_file_input = None

if upload_option == "Upload Files":
    uploaded_files = st.file_uploader("Upload .sql / .xml files", accept_multiple_files=True, type=['sql', 'xml'])
elif upload_option == "Upload Folder (Zip)":
    zip_file_input = st.file_uploader("Upload .zip file", type=['zip'])

# Dropdown for technology selection
tech_options_display = [
    "ABInitio", "ADF", "Alteryx", "Athena", "BigQuery", "BODS", "Cloudera (Impala)",
    "Datastage", "Greenplum", "Hive", "IBM DB2", "Informatica - Big Data Edition",
    "Informatica - PC", "Informatica Cloud", "MS SQL Server", "Netezza", "Oozie",
    "Oracle", "Oracle Data Integrator", "PentahoDI", "PIG", "Presto", "PySpark",
    "Redshift", "SAPHANA - CalcViews", "SAS", "Snowflake", "SPSS", "SQOOP", "SSIS",
    "SSRS", "Synapse", "Talend", "Teradata", "Vertica", "Others"
]

# --- VERIFIED MAPPING (CLI formats) ---
tech_options_cli_mapping = {
    "ABInitio": "ABInitio",
    "ADF": "ADF",
    "Alteryx": "Alteryx",
    "Athena": "Athena",
    "BigQuery": "BigQuery",
    "BODS": "BODS",
    "Cloudera (Impala)": "ClouderaImpala",
    "Datastage": "Datastage",
    "Greenplum": "Greenplum",
    "Hive": "Hive",
    "IBM DB2": "IBMDB2",
    "Informatica - Big Data Edition": "InformaticaBigDataEdition",
    "Informatica - PC": "Informatica - PC",
    "Informatica Cloud": "Informatica Cloud",
    "MS SQL Server": "MSSQLServer",
    "Netezza": "Netezza",
    "Oozie": "Oozie",
    "Oracle": "Oracle",
    "Oracle Data Integrator": "OracleDataIntegrator",
    "PentahoDI": "PentahoDI",
    "PIG": "PIG",
    "Presto": "Presto",
    "PySpark": "PySpark",
    "Redshift": "Redshift",
    "SAPHANA - CalcViews": "SAPHANACalcViews",
    "SAS": "SAS",
    "Snowflake": "Snowflake",
    "SPSS": "SPSS",
    "SQOOP": "SQOOP",
    "SSIS": "SSIS",
    "SSRS": "SSRS",
    "Synapse": "Synapse",
    "Talend": "Talend",
    "Teradata": "Teradata",
    "Vertica": "Vertica",
    "Others": "Generic"
}

selected_tech_display = st.selectbox("Select Source Technology", tech_options_display)
source_type_cli = tech_options_cli_mapping.get(selected_tech_display, "Generic")

# --- FOLDER SANITIZATION ---
source_type_folder = re.sub(r"[^\w]", "", source_type_cli)  # remove spaces & special characters

# Analyze button
if st.button("🔍 ANALYZE"):

    with st.spinner("Running analysis..."):
        local_input_path = None
        local_output_file = None

        try:
            BASE_TESTING_DIR.mkdir(parents=True, exist_ok=True)

            source_type_base_dir = BASE_TESTING_DIR.joinpath(source_type_folder)
            source_type_base_dir.mkdir(parents=True, exist_ok=True)

            input_dir_persistent = source_type_base_dir.joinpath("input")
            input_dir_persistent.mkdir(parents=True, exist_ok=True)

            output_dir_persistent = source_type_base_dir.joinpath("analysis")
            output_dir_persistent.mkdir(parents=True, exist_ok=True)

            # Step 1: Prepare local input directory based on method
            if upload_option == "Upload Files":
                for file_in_dir in input_dir_persistent.iterdir():
                    if file_in_dir.is_file():
                        file_in_dir.unlink()

                if not uploaded_files:
                    st.error("❌ No files uploaded. Please select files or change input method.")
                    st.stop()

                for file_obj in uploaded_files:
                    with open(input_dir_persistent.joinpath(file_obj.name), "wb") as f:
                        f.write(file_obj.read())
                local_input_path = input_dir_persistent
                st.info(f"Uploaded files saved to: {local_input_path}")
            elif upload_option == "Upload Folder (Zip)":
                if not zip_file_input:
                    st.error("❌ Please upload a zip file.")
                    st.stop()

                zip_extract_dir = input_dir_persistent.joinpath("unzipped_files")
                zip_extract_dir.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(zip_file_input, 'r') as zip_ref:
                    zip_ref.extractall(zip_extract_dir)

                local_input_path = zip_extract_dir
                st.info(f"Extracted zip file to: {local_input_path}")
            else:
                st.error("❌ Please upload files or provide a folder path.")
                st.stop()

            # Step 2: Define local output file with clean name
            local_output_file = output_dir_persistent.joinpath(f"{source_type_folder}-inventory.xlsx")
            st.info(f"Output report will be written to: {local_output_file}")

            # Step 3: Run LakeBridge CLI
            lakebridge_cmd = (
                f'databricks labs lakebridge analyze '
                f'--source-tech "{source_type_cli}" '
                f'--source-directory "{local_input_path}" '
                f'--report-file "{local_output_file}"'
            )

            st.info(f"Executing command: {lakebridge_cmd}")
            result = subprocess.run(lakebridge_cmd, shell=True, check=True, capture_output=True, text=True)

            if result.stdout:
                st.code(result.stdout, language='bash')
            if result.stderr:
                st.subheader("CLI Standard Error:")
                st.code(result.stderr, language='bash')

            # Step 4: Present the output
            if local_output_file.exists():
                with open(local_output_file, "rb") as f:
                    st.success("✅ Analysis completed successfully!")
                    st.download_button(
                        label="📥 Download analysis.xlsx",
                        data=f,
                        file_name=f"{source_type_folder}-inventory.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error("❌ Analysis completed but output file not found. Check CLI output above for errors.")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ CLI Error: Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
            if e.stdout:
                st.subheader("CLI Standard Output (on error):")
                st.code(e.stdout, language='bash')
            if e.stderr:
                st.subheader("CLI Standard Error (on error):")
                st.code(e.stderr, language='bash')
        except Exception as e:
            st.error(f"❌ Unexpected Error: {e}")
        finally:
            pass
