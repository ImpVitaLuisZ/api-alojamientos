from app import db


alojamiento_comodidad = db.Table(
    "alojamiento_comodidad",
    db.Column("alojamiento_id", db.Integer, db.ForeignKey("alojamientos.id"), primary_key=True),
    db.Column("comodidad_id", db.Integer, db.ForeignKey("comodidades.id"), primary_key=True),
)


class Comodidad(db.Model):
    __tablename__ = "comodidades"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    alojamientos = db.relationship(
        "Alojamiento", secondary=alojamiento_comodidad, back_populates="comodidades",
    )

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre}
