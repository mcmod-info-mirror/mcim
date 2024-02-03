# import json
# from typing import Any, Dict
# from pydantic import BaseModel

# def generate_pydantic_model(json_data: Dict[str, Any], model_name: str = "MyModel") -> str:
#     """
#     Generates Pydantic model code based on the given JSON data.

#     Args:
#         json_data (Dict[str, Any]): The JSON data to create the model from.
#         model_name (str, optional): Name of the Pydantic model. Defaults to "MyModel".

#     Returns:
#         str: Generated Python code for the Pydantic model.
#     """
#     fields = []
#     for key, value in json_data.items():
#         field_type = type(value).__name__
#         fields.append(f"{key}: {field_type}")

#     model_code = f"class {model_name}(BaseModel):\n"
#     model_code += "\n".join([f"    {field}" for field in fields])

#     return model_code

# # Example JSON data
# sample_json = {
#   "id": 0,
#   "gameId": 0,
#   "name": "string",
#   "slug": "string",
#   "url": "string",
#   "iconUrl": "string",
#   "dateModified": "2019-08-24T14:15:22Z",
#   "isClass": True,
#   "classId": 0,
#   "parentCategoryId": 0,
#   "displayIndex": 0
# }

# # Generate Pydantic model code
# generated_code = generate_pydantic_model(sample_json, model_name="Person")
# print(generated_code)

from app.service.curseforge import test
import asyncio

asyncio.run(test())