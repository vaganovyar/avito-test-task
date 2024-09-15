from enum import Enum


class ServiceType(str, Enum):
    CONSTRUCTION = "Construction"
    DELIVERY = "Delivery"
    MANUFACTURE = "Manufacture"
