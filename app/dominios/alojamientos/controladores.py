from flask import Blueprint, request

from app.dominios.alojamientos.servicios import AlojamientoServicio
from app.seguridad import requiere_token

alojamientos_bp = Blueprint("alojamientos", __name__)


@alojamientos_bp.get("")
def listar_alojamientos():
    return {"success": True, "data": AlojamientoServicio.listar()}, 200


@alojamientos_bp.get("/<int:alojamiento_id>")
def obtener_alojamiento(alojamiento_id):
    return {"success": True, "data": AlojamientoServicio.obtener(alojamiento_id).to_dict()}, 200


@alojamientos_bp.post("")
@requiere_token
def crear_alojamiento(usuario_id):
    alojamiento = AlojamientoServicio.crear(request.get_json(silent=True), usuario_id)
    return {"success": True, "data": alojamiento.to_dict()}, 201


@alojamientos_bp.patch("/<int:alojamiento_id>")
@requiere_token
def actualizar_alojamiento(alojamiento_id, usuario_id):
    alojamiento = AlojamientoServicio.actualizar(
        alojamiento_id, request.get_json(silent=True), usuario_id,
    )
    return {"success": True, "data": alojamiento.to_dict()}, 200


@alojamientos_bp.delete("/<int:alojamiento_id>")
@requiere_token
def eliminar_alojamiento(alojamiento_id, usuario_id):
    AlojamientoServicio.eliminar(alojamiento_id, usuario_id)
    return "", 204


@alojamientos_bp.patch("/<int:alojamiento_id>/comodidades")
@requiere_token
def asociar_comodidades(alojamiento_id, usuario_id):
    alojamiento = AlojamientoServicio.asociar_comodidades(
        alojamiento_id, request.get_json(silent=True), usuario_id,
    )
    return {"success": True, "data": alojamiento.to_dict()}, 200
