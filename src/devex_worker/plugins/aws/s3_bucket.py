import time


class ResourceHandler:
    def apply(self, resource):
        print(f"Creating AWS S3 Bucket: {resource['properties']['bucket_name']}")
        time.sleep(5)
        print(f"Created AWS S3 Bucket: {resource['properties']['bucket_name']}")
        return {"bucket_name": resource["properties"]["bucket_name"]}
