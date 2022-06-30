from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List, Dict
from datetime import date, datetime

from decimal import Decimal

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserModel(BaseModel):
    _id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    userId: int = Field(...)
    name: str = Field(...)
    email: EmailStr = Field(...)
    photo: str = Field(...)
    isActive: int = Field(...)
    level: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "userId": "2012101152",
                "name": "Fitri Andri Astuti",
                "email": "fitrengineer@gmail.com",
                "photo": "ok",
                "isActive": "1",
                "level": "0", #level roles: superadmin=0, admin=1, user=2
            }
        }

class UpdateUserModel(BaseModel):
    userId: Optional[int]
    name: Optional[str]
    email: Optional[EmailStr]
    photo: Optional[str]
    isActive: Optional[int]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Fitri Andri Astuti",
                "email": "fitrengineer@gmail.com",
                "photo": "ok",
                "isActive": "1",
            }
        }

class ProvinsiModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    prov: str = Field(...)
    nama: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "prov": "33",
                "nama": "JAWA TENGAH",
            }
        }

class KabupatenModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    prov: str = Field(...)
    kab: str = Field(...)
    nama: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "prov": "33",
                "kab": "13",
                "nama": "KARANGANYAR",
            }
        }






















