from app.dominios.comodidades.dtos import ComodidadDTO
from app.dominios.comodidades.modelos import Comodidad
from app.dominios.comodidades.repositorios import ComodidadRepositorio
from app.errores import ErrorAPI


class ComodidadServicio:
    @staticmethod
    def listar():
        return [comodidad.to_dict() for comodidad in ComodidadRepositorio.listar_todas()]

    @staticmethod
    def crear(datos):
        datos = ComodidadDTO().load(datos)
        if ComodidadRepositorio.obtener_por_nombre(datos["nombre"]):
            raise ErrorAPI("La comodidad ya existe.", 409)
        return ComodidadRepositorio.guardar(Comodidad(**datos))
