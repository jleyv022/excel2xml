import streamlit as st
from streamlit import caching
import pandas as pd
from lxml import etree as et
from zipfile import ZipFile
import shutil
import os

st.title("iTunes XML Generator 🍏")
st.markdown("Create iTunes Episodic XML's by uploading an excel metadata spreadsheets")
st.markdown("More Details about iTunes Package TV Specification 5.3.6  >>> [Click Here](https://help.apple.com/itc/tvspec/#/apdATD1E170-D1E1A1303-D1E170A1126)")

col1, col2 = st.columns(2)
with col1:
    share = st.checkbox("Asset Share (optional)", key="disabled")
    bundle = st.checkbox("Bundle Only (optional)", key="true")

with col2:
    option = st.radio(
        "Select a Locale Name",
        ("en-CA", "en-AU", "en-GB", "de-DE", "fr-FR")
    )

uploaded_file = st.file_uploader("Create XML")
if uploaded_file is not None:
    dataframe = pd.read_excel(uploaded_file)
    tree = et.parse(f'TEMPLATES/iTunes_TV_EPISODE_TEMPLATE_v5-3_{option}.xml')
    template_root = tree.getroot()
    package_folder = "iTunes Package with XML"
    os.makedirs(package_folder)
    xml_folder = "XML"
    os.makedirs(xml_folder)

    for index, row in dataframe.iterrows():
        if index > 2:
            package_name = str(row['Unnamed: 23'])
            full_sale_date = str(row['Unnamed: 34'])
            zip_name = str(row['ITUNES'])
            
            if "en" in option:
                template_root[2][16][0][0][1].text = package_name+'.mov'#mov file name
                template_root[2][16][0][1][1].text = package_name+'.scc'#scc file name
                template_root[2][18][0][1].text = full_sale_date[0:10]
            else:
                template_root[2][15][0][0][1].text = package_name+".mov"#mov file name
                template_root[2][17][0][1].text = full_sale_date[0:10]
            rating = template_root[2][14][0].attrib
            rating['code'] = str(row['Unnamed: 7'])
            
            for container_id in template_root[2].iter('{http://apple.com/itunes/importer}container_id'):
                container_id.text = str(row['ITUNES'])
                
            for container_position in template_root[2].iter('{http://apple.com/itunes/importer}container_position'):
                container_position.text = str(row['Unnamed: 24'])
                
            for vendor_id in template_root[2].iter('{http://apple.com/itunes/importer}vendor_id'):
                vendor_id.text = str(row['Unnamed: 23'])
            
            for episode_production_number in template_root[2].iter('{http://apple.com/itunes/importer}episode_production_number'):
                episode_production_number.text = str(row['TITLE'])
            
            for title in template_root[2].iter('{http://apple.com/itunes/importer}title'):
                title.text = str(row['Unnamed: 3'])
                
            for studio_release_title in template_root[2].iter('{http://apple.com/itunes/importer}studio_release_title'):
                studio_release_title.text = str(row['Unnamed: 4'])
            
            for description in template_root[2].iter('{http://apple.com/itunes/importer}description'):
                description.text = str(row['Unnamed: 5'])
            
            for release_date in template_root[2].iter('{http://apple.com/itunes/importer}release_date'):
                full_date = str(row['Unnamed: 14'])
                release_date.text = full_date[0:10]
                
            for copyright in template_root[2].iter('{http://apple.com/itunes/importer}copyright_cline'):
                copyright.text = str(row['Unnamed: 15'])

            package = f'{package_name}.itmsp'
            xml = "metadata.xml"
            os.makedirs(package)
            package_path = os.path.abspath(package)    
            tree.write(f'{package_name}.xml', encoding="utf-8", xml_declaration=True)
            tree.write(xml, encoding="utf-8", xml_declaration=True)
            xml_path = os.path.abspath(xml)
            shutil.move(xml_path, package_path)
            shutil.move(os.path.abspath(package_path), os.path.abspath(package_folder))
            shutil.move(os.path.abspath(f'{package_name}.xml'), os.path.abspath(xml_folder))

zip_name = container_id.text
os.mkdir(zip_name)
shutil.move(os.path.abspath(package_folder), os.path.abspath(zip_name))
shutil.move(os.path.abspath(xml_folder), os.path.abspath(zip_name))
shutil.make_archive(zip_name, 'zip', os.path.abspath(zip_name))

with open(zip_name+'.zip', 'rb') as f:
    if st.download_button('Download Zip', f, file_name=zip_name+'.zip'):
        caching.clear_cache()
