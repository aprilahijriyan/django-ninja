import pytest
from typing import List
from ninja import Body, NinjaAPI, Schema
from django.test import Client, override_settings


api = NinjaAPI()


class Payload(Schema):
    i: int
    f: float


class Response(Schema):
    i: int
    f: float


@api.post("/test", response=Response)
def method(request, data: Payload):
    return data.dict()


@api.post("/test_list", response=List[Response])
def method_list_response(request, data: List[Payload]):
    return []


@api.post("/test-body", response=List[Response])
def method_body(request, i: int = Body(...), f: float = Body(...)):
    return [i, f]


def test_schema_views(client: Client):
    assert client.get("/api/").status_code == 404
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200


def test_schema_views_no_INSTALLED_APPS(client: Client):
    "Making sure that cdn and included js works fine"
    from django.conf import settings

    # removing ninja from settings:
    INSTALLED_APPS = [i for i in settings.INSTALLED_APPS if i != "ninja"]

    @override_settings(INSTALLED_APPS=INSTALLED_APPS)
    def call_docs():
        assert client.get("/api/docs").status_code == 200

    call_docs()


def test_schema():
    schema = api.get_openapi_schema()
    from pprint import pprint

    # --------------------------------------------------------------
    method = schema["paths"]["/api/test"]["post"]

    assert method["requestBody"] == {
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/Payload"}}
        },
        "required": True,
    }
    assert method["responses"] == {
        200: {
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Response"}
                }
            },
            "description": "OK",
        }
    }

    # --------------------------------------------------------------
    method_list = schema["paths"]["/api/test_list"]["post"]

    assert method_list["requestBody"] == {
        "content": {
            "application/json": {
                "schema": {
                    "items": {"$ref": "#/components/schemas/Payload"},
                    "title": "Data",
                    "type": "array",
                }
            }
        },
        "required": True,
    }
    assert method_list["responses"] == {
        200: {
            "content": {
                "application/json": {
                    "schema": {
                        "items": {"$ref": "#/components/schemas/Response"},
                        "title": "Response",
                        "type": "array",
                    }
                }
            },
            "description": "OK",
        }
    }

    assert schema["components"]["schemas"] == {
        "Payload": {
            "properties": {
                "f": {"title": "F", "type": "number"},
                "i": {"title": "I", "type": "integer"},
            },
            "required": ["i", "f"],
            "title": "Payload",
            "type": "object",
        },
        "Response": {
            "properties": {
                "f": {"title": "F", "type": "number"},
                "i": {"title": "I", "type": "integer"},
            },
            "required": ["i", "f"],
            "title": "Response",
            "type": "object",
        },
    }

    # --------------------------------------------------------------
    method_list = schema["paths"]["/api/test-body"]["post"]

    assert method_list["requestBody"] == {
        'content': {
            'application/json': {
                'schema': {
                    "properties": {
                        "f": {"title": "F", "type": "number"},
                        "i": {"title": "I", "type": "integer"},
                    },
                    "required": ["i", "f"],
                    "title": "BodyParams",
                    "type": "object",
                }
            }
        },
        'required': True
    }
    assert method_list["responses"] == {
        200: {
            "content": {
                "application/json": {
                    "schema": {
                        "items": {"$ref": "#/components/schemas/Response"},
                        "title": "Response",
                        "type": "array",
                    }
                }
            },
            "description": "OK",
        }
    }


def test_unique_operation_ids():

    api = NinjaAPI()

    @api.get("/1")
    def same_name(request):
        pass

    @api.get("/2")
    def same_name(request):
        pass

    with pytest.warns(UserWarning):
        schema = api.get_openapi_schema()
