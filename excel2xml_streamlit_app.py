import streamlit as st
import pandas as pd
from lxml import etree as et
import shutil
import os

st.title("iTunes XML Generator 🍏")
st.markdown("Create iTunes Episodic XML's by uploading an Excel metadata spreadsheet")
st.markdown("More Details about iTunes Package TV Specification 5.3.6  >>> [Click Here](https://help.apple.com/itc/tvspec/#/apdATD1E170-D1E1A1303-D1E170A1126)")

col1, col2 = st.columns(2)
with col1:
    share = st.checkbox("Asset Share (optional)")
    bundle = st.checkbox("Bundle Only (optional)")
    with open('TEMPLATES/XXXXX_SX_Metadata_XX_iTunes_TV.xlsx', 'rb') as my_file:
        st.download_button(label='Download Excel Template', data=my_file, file_name='XXXXX_SX_Metadata_XX_iTunes_TV.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

with col2:
    option = st.radio("Select a Locale Name", ("en-CA", "en-AU", "en-GB", "de-DE", "fr-FR", "us-US"))

uploaded_file = st.file_uploader("Upload Excel Metadata File")

if uploaded_file:
    try:
        # Read Excel with openpyxl (better compatibility)
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        if df.empty:
            st.error("Error: The uploaded Excel file is empty or not read properly.")
            st.stop()

        # Display column names for debugging
        st.write("**Columns Found in Uploaded File:**", df.columns.tolist())

        # Ensure required columns exist
        required_cols = {
            'package_name': 'Unnamed: 23',
            'rating_code': 'Unnamed: 7',
            'asset_share_id': 'Unnamed: 27',
            'container_position': 'Unnamed: 24',
            'title': 'TITLE',
            'itunes_id': 'ITUNES',
            'display_title': 'Unnamed: 3',
            'studio_title': 'Unnamed: 4',
            'description': 'Unnamed: 5',
            'release_date': 'Unnamed: 14',
            'copyright': 'Unnamed: 15',
            'sales_date': 'Unnamed: 34'
        }

        # Check if all required columns exist
        missing_cols = [key for key, col in required_cols.items() if col not in df.columns]
        if missing_cols:
            st.error(f"Error: Missing columns in the uploaded file: {missing_cols}")
            st.stop()

        # Apply the correct naming scheme
        if share:
            option += "_ASSET_SHARE"

        # Load XML template
        xml_template_path = f'TEMPLATES/iTunes_TV_EPISODE_TEMPLATE_v5-3_{option}.xml'
        if not os.path.exists(xml_template_path):
            st.error(f"Error: XML template for {option} not found.")
            st.stop()
        
        tree = et.parse(xml_template_path)
        template_root = tree.getroot()

        # Create directories
        package_folder = "iTunes Package with XML"
        xml_folder = "XML"
        os.makedirs(package_folder, exist_ok=True)
        os.makedirs(xml_folder, exist_ok=True)

        # Process each row
        for index, row in df.iterrows():
            if index < 3:  # Skip first few rows if they are headers or empty
                continue

            package_name = str(row[required_cols['package_name']]).strip()
            if not package_name or package_name.lower() == "nan":
                st.warning(f"Skipping row {index + 1}: Invalid package name.")
                continue

            # Update XML fields
            template_root[2][14][0].attrib['code'] = str(row[required_cols['rating_code']]).strip()

            if bundle:
                for bundle_only in template_root[2].iter('{http://apple.com/itunes/importer}products'):
                    bundle_only[0][3].text = 'true'

            if share:
                for shared_asset_id in template_root[2].iter('{http://apple.com/itunes/importer}share_assets'):
                    shared_asset_id.attrib['vendor_id'] = str(row[required_cols['asset_share_id']]).strip()

            # Set MOV and SCC filenames
            if "en" in option and "_ASSET_SHARE" not in option:
                template_root[2][16][0][0][1].text = package_name + '.mov'
                template_root[2][16][0][1][1].text = package_name + '.scc'
            else:
                template_root[2][15][0][0][1].text = package_name + ".mov"

            # Populate XML fields
            for field, xml_tag in [
                ('itunes_id', 'container_id'),
                ('container_position', 'container_position'),
                ('package_name', 'vendor_id'),
                ('title', 'episode_production_number'),
                ('display_title', 'title'),
                ('studio_title', 'studio_release_title'),
                ('description', 'description'),
                ('release_date', 'release_date'),
                ('copyright', 'copyright_cline'),
            ]:
                value = str(row[required_cols[field]]).strip()
                for element in template_root[2].iter(f'{{http://apple.com/itunes/importer}}{xml_tag}'):
                    element.text = value

            # Process sales start date
            full_sale_date = str(row[required_cols['sales_date']]).strip()
            for sales_start_date in template_root[2].iter('{http://apple.com/itunes/importer}products'):
                sales_start_date[0][1].text = full_sale_date[:10]  # Ensure only YYYY-MM-DD

            # Save XML
            xml_filename = f"{package_name}.xml"
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
            shutil.move(xml_filename, xml_folder)

        # ZIP XML Folder
        zip_name = "XML_Files"
        shutil.make_archive(zip_name, 'zip', xml_folder)

        # Provide download link
        with open(zip_name + ".zip", 'rb') as f:
            st.download_button('Download XML Zip', f, file_name=zip_name + ".zip")

        st.success("✅ XML files generated and ready for download.")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")

else:
    st.info("📂 Please upload an Excel file to continue.")
