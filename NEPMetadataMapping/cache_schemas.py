import urllib.request
import logging
import json
import NEPMetadataMapping.schemas_collector

class Cache_Schemas():

    def __init__(self, json_schema: dict) -> None:
        """Class instantiation.
        """
        self.json_schema = json_schema
    
    @classmethod
    def cache_schema(cls, map_dict: dict) -> dict:
        """Cache, or set the schema that is referenced by the map json document via the uri key and return it as dictionary.

        Args:
            map_dict (dict): _description_

        Raises:
            KeyError: No uri as key provided in the input dictionary.

        Returns:
            dict: The schema as dictionary.
        """
        try:
            if NEPMetadataMapping.schemas_collector.schemas_collector_instance.get_uri(map_dict["uri"]):
                json_schema = NEPMetadataMapping.schemas_collector.schemas_collector_instance.get_schema(map_dict["uri"])
            else:
                with urllib.request.urlopen(map_dict["uri"]) as url:
                    json_schema = json.load(url)
                NEPMetadataMapping.schemas_collector.schemas_collector_instance.add_schema(map_dict["uri"], json_schema)

        except KeyError as e:
            logging.error("Schema not accessible.")

        return cls(json_schema)