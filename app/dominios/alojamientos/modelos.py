from datetime import datetime

from app import db
from app.dominios.comodidades.modelos import alojamiento_comodidad


class Alojamiento(db.Model):
    __tablename__ = "alojamientos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio_noche = db.Column(db.Numeric(10, 2), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario = db.relationship("Usuario", back_populates="alojamientos")

    comodidades = db.relationship(
        "Comodidad", secondary=alojamiento_comodidad, back_populates="alojamientos",
        order_by="Comodidad.id",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "precio_noche": float(self.precio_noche),
            "ciudad": self.ciudad,
            "usuario_id": self.usuario_id,
            "comodidades": [comodidad.to_dict() for comodidad in self.comodidades],
        }
