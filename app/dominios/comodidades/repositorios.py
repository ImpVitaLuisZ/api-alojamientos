from sqlalchemy.exc import IntegrityError

from app import db
from app.dominios.comodidades.modelos import Comodidad
from app.errores import ErrorAPI


class ComodidadRepositorio:
    @staticmethod
    def listar_todas():
        return db.session.query(Comodidad).order_by(Comodidad.id).all()

    @staticmethod
    def obtener_por_nombre(nombre):
        return db.session.query(Comodidad).filter_by(nombre=nombre).first()

    @staticmethod
    def obtener_por_ids(ids):
        return db.session.query(Comodidad).filter(Comodidad.id.in_(ids)).order_by(Comodidad.id).all()

    @staticmethod
    def guardar(comodidad):
        db.session.add(comodidad)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            if ComodidadRepositorio.obtener_por_nombre(comodidad.nombre):
                raise ErrorAPI("La comodidad ya existe.", 409) from None
            raise
        return comodidad
