import sys
import NEPMetadataMapping.dicom_mapping

map_json_path = sys.argv[1]

metadata_files_location = sys.argv[2]

mapped_metadata = sys.argv[3]

NEPMetadataMapping.Dicom_Mapping(map_json_path, metadata_files_location, mapped_metadata)
