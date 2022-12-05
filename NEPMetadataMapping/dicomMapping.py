import json
from .metadataSchemaReader import MetadataSchemaReader
from .metadataReader import MetadataReader
from .mapMRISchema import Map_MRI_Schema
from .attributeMapping import AttributeMapping
from .dicomReader import DicomReader
import urllib.request
import logging
import NEPMetadataMapping.schemasCollector
import time

class DicomMapping:
    
    def __init__(self, map_json_path: str, metadata_files_location: str, additional_attributes_list: list, mapped_metadata='mapped_metadata1.json') -> None:
        """Instantiates the class and calls the method to execute all steps for mapping.

        Args:
            map_json (json): A json based map of the attribute assignments for mapping.
            metadata_files_location (str): The directory where the dicom files of a study are stored.
            mapped_metadata (str, optional): The resulting json file. Defaults to 'mapped_metadata.json'.
        """

        with open(map_json_path, 'r') as f:
            map_dict = json.load(f)
        self.map_dict=map_dict
        self.metadata_files_location = metadata_files_location
        self.additional_attributes_list=additional_attributes_list
        self.mapped_metadata=mapped_metadata
        #self.execute_steps(map_dict, metadata_files_location, additional_attributes_list, mapped_metadata)

    def execute_steps(self, map_dict: dict, metadata_files_location: str, additional_attributes_list: list, mapped_metadata: str) -> None:
        """Executes all steps for mapping a dicom study to a json schema.

        Args:
            map_dict (dict): The map of the attribute assignments for mapping as a dictionary.
            metadata_files_location (str): The directory where the dicom files of a study are stored.
            mapped_metadata (str): The resulting json file.
        """

        json_schema=self.cache_schemas(map_dict)
        schema_skeleton = MetadataSchemaReader(json_schema)
        schema_skeleton = schema_skeleton.json_object_search(schema_skeleton.schema)
        dicom_object = MetadataReader(metadata_files_location)
        self.validate_study(dicom_object)
        dicom_series_list = dicom_object.all_dicom_series

        study_map = AttributeMapping.mapping_from_object(dicom_series_list[0].__dict__, map_dict, "study")
        series_maps_list = []
        for series in dicom_series_list:
            series_map = AttributeMapping.mapping_from_object(series.__dict__, map_dict, "series")
            for additional_attributes in additional_attributes_list:
                all_attributes_map_list=self.series_extension(map_dict, additional_attributes, series)
                kwargs={f"{additional_attributes}":all_attributes_map_list}
                series_map.updateMap(**kwargs)
            series_maps_list.append(series_map)
        study_map.updateMap(series=series_maps_list)
        
        map_mri_schema = Map_MRI_Schema(schema_skeleton, list(schema_skeleton.keys()), study_map, None)
        filled_schema = map_mri_schema.fill_json_object(map_mri_schema.schema_skeleton, map_mri_schema.key_list, map_mri_schema.map, map_mri_schema.main_key)
        with open(mapped_metadata, 'w') as f:
            json.dump(filled_schema, f)

    def cache_schemas(self, map_dict: dict) -> dict:
        """Cache, or set the schema that is referenced by the map json document via the uri key and return it as dictionary.

        Args:
            map_dict (dict): _description_

        Raises:
            KeyError: No uri as key provided in the input dictionary.

        Returns:
            dict: The schema as dictionary.
        """
        try:
            if NEPMetadataMapping.schemasCollector.schemasCollectorInstance.get_uri(map_dict["uri"]):
                jsonSchema = NEPMetadataMapping.schemasCollector.schemasCollectorInstance.get_schema(map_dict["uri"])
            else:
                with urllib.request.urlopen(map_dict["uri"]) as url:
                    jsonSchema = json.load(url)
                NEPMetadataMapping.schemasCollector.schemasCollectorInstance.add_schema(map_dict["uri"], jsonSchema)

        except KeyError as e:
            logging.error("Schema not accessible.")

        return jsonSchema

    def validate_study(self, dicom_object: MetadataReader) -> None:
        """Validate that all dicom files (series) of a study have the same Study Instance UID.

        Args:
            dicom_object (MetadataReader): The object that contains the dicom metadata attributes.

        Raises:
            Exception: Strings are not the same.
        """
        allStudyInstanceUIDs = []
        for series in dicom_object.all_dicom_series:
            allStudyInstanceUIDs.append(series.studyInstanceUid)

        if all(series == allStudyInstanceUIDs[0] for series in allStudyInstanceUIDs) == True:
            pass
        else:
            raise Exception('Files are not from the same study.')

    def series_extension(self, map_dict: dict, map_attribute: str, series: DicomReader) -> list:
        """Extends the mapped attributes of a series object by an attribute that has a list of objects as values, using the keywords of the provided map.

        Args:
            map_dict (dict): Map that contains the attribute assignments for the dicom metadata and the schema.
            map_attribute (str): The attribute in the map that contains the mapping assignments.
            series (DicomReader): The series which is extended.

        Returns:
            list: A list of objects with the mapped attributes.
        """
        all_attributes_map_list=[]
        numer_of_sub_attributes=len(map_dict[map_attribute])
        number_of_additional_objects=len(series.__dict__[list(map_dict[map_attribute].keys())[0]])
        
        for object_number in range(0, number_of_additional_objects):
            temp_image_attributes={}
            for attribute_number in range(0, numer_of_sub_attributes):
                temp_image_attributes[list(map_dict[map_attribute].keys())[attribute_number]]=series.__dict__[list(map_dict[map_attribute].keys())[attribute_number]][object_number]
            attributes_map = AttributeMapping.mapping_from_object(temp_image_attributes, map_dict, map_attribute)
            all_attributes_map_list.append(attributes_map)
        return all_attributes_map_list
