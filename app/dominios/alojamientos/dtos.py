from decimal import Decimal

from marshmallow import Schema, ValidationError, fields, validate


def texto_no_vacio(valor):
    if not valor.strip():
        raise ValidationError("El texto no puede estar vacío.")


def precio_valido(valor):
    if valor < Decimal("0.01") or valor > Decimal("99999999.99"):
        raise ValidationError("El precio debe estar entre 0.01 y 99999999.99.")


class AlojamientoDTO(Schema):
    titulo = fields.String(required=True, validate=[texto_no_vacio, validate.Length(max=200)])
    descripcion = fields.String(required=True, validate=texto_no_vacio)
    precio_noche = fields.Decimal(required=True, allow_nan=False, validate=precio_valido)
    ciudad = fields.String(required=True, validate=[texto_no_vacio, validate.Length(max=100)])


class ActualizarAlojamientoDTO(AlojamientoDTO):
    def __init__(self, **kwargs):
        super().__init__(partial=True, **kwargs)
        for campo in self.fields.values():
            campo.allow_none = True
