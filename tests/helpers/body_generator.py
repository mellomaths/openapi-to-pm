class BodyGenerator:

    @staticmethod
    def openapi_spec():
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "API Orders",
                "description": "API to handle Orders operations.",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Production"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {}
            }
        }