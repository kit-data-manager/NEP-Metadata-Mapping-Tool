import sys
import NEPMetadataMapping.dicomMapping

map = sys.argv[1]

metadata = sys.argv[2]

mappedMetadata = sys.argv[3]

NEPMetadataMapping.DicomMapping(map, metadata, mappedMetadata)
