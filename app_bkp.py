import streamlit as st
import os
import subprocess
from pathlib import Path

# ✅ Writable folder in Databricks Apps
BASE_TESTING_DIR = Path("/tmp/lakebridge-testing-files")

# Title
st.title("🧠 LakeBridge Analyzer")

# 📂 File input section
upload_option = st.radio("Choose input method:", ["Upload Files", "Enter Folder Path"])
uploaded_files = None
folder_path_input = None

if upload_option == "Upload Files":
    uploaded_files = st.file_uploader("Upload .sql / .xml files", accept_multiple_files=True, type=['sql', 'xml'])
else:
    folder_path_input = st.text_input("Enter full folder path (inside /tmp)")

# 🔎 Source Tech Selection
tech_options_display = [
    "ABInitio", "ADF", "Alteryx", "Athena", "BigQuery", "BODS", "Cloudera (Impala)",
    "Datastage", "Greenplum", "Hive", "IBM DB2", "Informatica - Big Data Edition",
    "Informatica - PC", "Informatica Cloud", "MS SQL Server", "Netezza", "Oozie",
    "Oracle", "Oracle Data Integrator", "PentahoDI", "PIG", "Presto", "PySpark",
    "Redshift", "SAPHANA - CalcViews", "SAS", "Snowflake", "SPSS", "SQOOP", "SSIS",
    "SSRS", # Added SSRS as per your list
    "Synapse", "Talend", "Teradata", "Vertica", "Others"
]
tech_options_cli_mapping = {
    "ABInitio": "ABInitio",
    "ADF": "ADF",
    "Alteryx": "Alteryx",
    "Athena": "Athena",
    "BigQuery": "BigQuery",
    "BODS": "BODS",
    "Cloudera (Impala)": "ClouderaImpala", # Common pattern: remove spaces/special chars
    "Datastage": "Datastage",
    "Greenplum": "Greenplum",
    "Hive": "Hive",
    "IBM DB2": "IBMDB2", # Common pattern: remove spaces
    "Informatica - Big Data Edition": "InformaticaBigDataEdition", # Common pattern: remove spaces/hyphens
    "Informatica - PC": "Informatica - PC", # This is the most likely candidate for your previous error
    "Informatica Cloud": "Informatica Cloud",
    "MS SQL Server": "MSSQLServer", # Common pattern: remove spaces
    "Netezza": "Netezza",
    "Oozie": "Oozie",
    "Oracle": "Oracle",
    "Oracle Data Integrator": "OracleDataIntegrator",
    "PentahoDI": "PentahoDI",
    "PIG": "PIG",
    "Presto": "Presto",
    "PySpark": "PySpark",
    "Redshift": "Redshift",
    "SAPHANA - CalcViews": "SAPHANACalcViews", # Common pattern: remove spaces/hyphens
    "SAS": "SAS",
    "Snowflake": "Snowflake",
    "SPSS": "SPSS",
    "SQOOP": "SQOOP",
    "SSIS": "SSIS",
    "SSRS": "SSRS", # Added as per your explicit list
    "Synapse": "Synapse",
    "Talend": "Talend",
    "Teradata": "Teradata",
    "Vertica": "Vertica",
    "Others": "Generic" # Assuming "Generic" is the string for 'Others'
}
selected_tech_display = st.selectbox("Select Source Technology", tech_options_display)
source_type_cli = tech_options_cli_mapping.get(selected_tech_display, "Generic")

# 🚀 Analysis trigger
if st.button("🔍 ANALYZE"):
    with st.spinner("Running LakeBridge analysis..."):

        try:
            # 🌿 Setup directories
            source_type_base_dir = BASE_TESTING_DIR.joinpath(source_type_cli)
            input_dir_persistent = source_type_base_dir.joinpath("input")
            output_dir_persistent = source_type_base_dir.joinpath("analysis")
            input_dir_persistent.mkdir(parents=True, exist_ok=True)
            output_dir_persistent.mkdir(parents=True, exist_ok=True)

            # 📥 Handle Uploads
            if upload_option == "Upload Files":
                if not uploaded_files:
                    st.error("❌ No files uploaded.")
                    st.stop()

                # Clear old inputs
                for f in input_dir_persistent.glob("*"):
                    f.unlink()

                for file_obj in uploaded_files:
                    file_path = input_dir_persistent.joinpath(file_obj.name)
                    with open(file_path, "wb") as f:
                        f.write(file_obj.read())
                local_input_path = input_dir_persistent
                st.success(f"✅ Saved {len(uploaded_files)} file(s).")

            elif upload_option == "Enter Folder Path":
                folder_path_obj = Path(folder_path_input)
                if not folder_path_obj.is_absolute():
                    folder_path_obj = BASE_TESTING_DIR.joinpath(folder_path_obj)
                if not folder_path_obj.is_dir():
                    st.error("❌ Invalid folder path.")
                    st.stop()
                local_input_path = folder_path_obj
            else:
                st.error("❌ Invalid input option.")
                st.stop()

            # 📝 Report file path
            local_output_file = output_dir_persistent.joinpath(f"{source_type_cli}-inventory.xlsx")
            st.info(f"📤 Output will be saved to: {local_output_file}")

            # 🧪 Run CLI
            lakebridge_cmd = (
                f'databricks labs lakebridge analyze '
                f'--source-tech "{source_type_cli}" '
                f'--source-directory "{local_input_path}" '
                f'--report-file "{local_output_file}"'
            )
            st.code(f"Running command: {lakebridge_cmd}", language='bash')
            result = subprocess.run(lakebridge_cmd, shell=True, check=True, capture_output=True, text=True)

            if result.stdout:
                st.subheader("📄 CLI Output:")
                st.code(result.stdout, language='bash')
            if result.stderr:
                st.subheader("⚠️ CLI Warnings:")
                st.code(result.stderr, language='bash')

            # 📥 File download
            if local_output_file.exists():
                with open(local_output_file, "rb") as f:
                    st.download_button(
                        label="📥 Download analysis report",
                        data=f,
                        file_name=f"{source_type_cli}-inventory.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("✅ Analysis completed!")
            else:
                st.error("❌ Report file not found after CLI execution.")

        except subprocess.CalledProcessError as e:
            st.error(f"⚠️ CLI error: {e}")
            if e.stderr:
                st.code(e.stderr, language='bash')
        except Exception as e:
            st.error(f"⚠️ Unexpected error: {e}")
