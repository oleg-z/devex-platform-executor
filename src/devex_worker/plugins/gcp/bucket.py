import time


class ResourceHandler:
    def apply(self, resource):
        print(f"Creating GCP Bucket: {resource['properties']['bucket_name']}")
        print(f"Created GCP Bucket: {resource['properties']['bucket_name']}")
        return {"bucket_name": resource["properties"]["bucket_name"]}
