from marshmallow import Schema, ValidationError, fields, validate


def nombre_no_vacio(valor):
    if not valor.strip():
        raise ValidationError("El nombre no puede estar vacío.")


class ComodidadDTO(Schema):
    nombre = fields.String(required=True, validate=[nombre_no_vacio, validate.Length(max=100)])


class AsociarComodidadesDTO(Schema):
    comodidades_ids = fields.List(
        fields.Integer(strict=True, validate=validate.Range(min=1)), required=True,
    )
