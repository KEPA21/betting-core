from pydantic import BaseModel, ConfigDict


class APISchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
