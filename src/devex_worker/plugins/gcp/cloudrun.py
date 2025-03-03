import yaml


class ResourceHandler:
    def apply(self, resource):
        print(f"Creating GCP cloud run: {resource['properties']['name']}")
        print("Additional properties:")
        print(yaml.dump(resource["properties"], indent=4))
        return {"name": resource["properties"]["name"]}
