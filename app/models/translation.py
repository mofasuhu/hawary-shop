from app.extensions import db


class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(1020), unique=True, nullable=False)
    value_en = db.Column(db.Text, nullable=False)
    value_ar = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Translation {self.key}: {self.value_en} / {self.value_ar}>"


class LowercaseDict(dict):
    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def get(self, key, default=None):
        return super().get(key.lower(), default)

    def __contains__(self, key):
        return super().__contains__(key.lower())
