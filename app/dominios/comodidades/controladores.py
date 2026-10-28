from flask import Blueprint, request

from app.dominios.comodidades.servicios import ComodidadServicio
from app.seguridad import requiere_admin

comodidades_bp = Blueprint("comodidades", __name__)


@comodidades_bp.get("")
def listar_comodidades():
    return {"success": True, "data": ComodidadServicio.listar()}, 200


@comodidades_bp.post("")
@requiere_admin
def crear_comodidad(usuario_id):
    comodidad = ComodidadServicio.crear(request.get_json(silent=True))
    return {"success": True, "data": comodidad.to_dict()}, 201
