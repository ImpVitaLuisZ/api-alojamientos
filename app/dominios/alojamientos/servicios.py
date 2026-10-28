from app.dominios.alojamientos.dtos import ActualizarAlojamientoDTO, AlojamientoDTO
from app.dominios.alojamientos.modelos import Alojamiento
from app.dominios.alojamientos.repositorios import AlojamientoRepositorio
from app.dominios.usuarios.repositorios import UsuarioRepositorio
from app.dominios.comodidades.dtos import AsociarComodidadesDTO
from app.dominios.comodidades.repositorios import ComodidadRepositorio
from app.errores import ErrorAPI


class AlojamientoServicio:
    @staticmethod
    def _usuario(usuario_id):
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if not usuario:
            raise ErrorAPI("Usuario no autenticado.", 401)
        return usuario

    @staticmethod
    def obtener(alojamiento_id):
        alojamiento = AlojamientoRepositorio.obtener_por_id(alojamiento_id)
        if not alojamiento:
            raise ErrorAPI("Alojamiento no encontrado.", 404)
        return alojamiento

    @staticmethod
    def listar():
        return [alojamiento.to_dict() for alojamiento in AlojamientoRepositorio.listar_todos()]

    @classmethod
    def crear(cls, datos, usuario_id):
        cls._usuario(usuario_id)
        datos = AlojamientoDTO().load(datos)
        return AlojamientoRepositorio.guardar(Alojamiento(**datos, usuario_id=usuario_id))

    @classmethod
    def _autorizado(cls, alojamiento_id, usuario_id):
        usuario = cls._usuario(usuario_id)
        alojamiento = cls.obtener(alojamiento_id)
        if alojamiento.usuario_id != usuario.id and usuario.rol != "admin":
            raise ErrorAPI("Se requiere ser propietario o administrador.", 403)
        return alojamiento

    @classmethod
    def actualizar(cls, alojamiento_id, datos, usuario_id):
        alojamiento = cls._autorizado(alojamiento_id, usuario_id)
        datos = ActualizarAlojamientoDTO().load(datos)
        for campo, valor in datos.items():
            if valor is not None:
                setattr(alojamiento, campo, valor)
        return AlojamientoRepositorio.guardar(alojamiento)

    @classmethod
    def eliminar(cls, alojamiento_id, usuario_id):
        alojamiento = cls._autorizado(alojamiento_id, usuario_id)
        AlojamientoRepositorio.eliminar(alojamiento)

    @classmethod
    def asociar_comodidades(cls, alojamiento_id, datos, usuario_id):
        alojamiento = cls._autorizado(alojamiento_id, usuario_id)
        datos = AsociarComodidadesDTO().load(datos)
        ids = set(datos["comodidades_ids"])
        comodidades = ComodidadRepositorio.obtener_por_ids(ids)
        if len(comodidades) != len(ids):
            raise ErrorAPI("Una o más comodidades no existen.", 400)
        alojamiento.comodidades = comodidades
        return AlojamientoRepositorio.guardar(alojamiento)
