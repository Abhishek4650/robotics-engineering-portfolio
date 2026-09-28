"""mock adsk.core -- see adsk/__init__.py"""
import numpy as np


class Point3D:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    @staticmethod
    def create(x=0.0, y=0.0, z=0.0):
        return Point3D(x, y, z)

    def distanceTo(self, o):
        return float(np.linalg.norm([self.x - o.x, self.y - o.y, self.z - o.z]))

    def copy(self):
        return Point3D(self.x, self.y, self.z)

    def asArray(self):
        return [self.x, self.y, self.z]


class Vector3D(Point3D):
    @staticmethod
    def create(x=0.0, y=0.0, z=0.0):
        return Vector3D(x, y, z)


class Matrix3D:
    def __init__(self):
        self.m = np.eye(4)

    @staticmethod
    def create():
        return Matrix3D()

    def setWithCoordinateSystem(self, origin, xAxis, yAxis, zAxis):
        # Fusion: the matrix that takes the world frame onto this coordinate system
        self.m = np.eye(4)
        self.m[:3, 0], self.m[:3, 1], self.m[:3, 2] = xAxis.asArray(), yAxis.asArray(), zAxis.asArray()
        self.m[:3, 3] = origin.asArray()
        R = self.m[:3, :3]
        if np.abs(R.T @ R - np.eye(3)).max() > 1e-9 or np.linalg.det(R) < 0:
            raise RuntimeError("Matrix3D: axes are not a right-handed orthonormal set")
        return True


class ObjectCollection:
    def __init__(self):
        self._items = []

    @staticmethod
    def create():
        return ObjectCollection()

    def add(self, x):
        self._items.append(x)
        return True

    @property
    def count(self):
        return len(self._items)

    def item(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)


class ValueInput:
    def __init__(self, v):
        self.realValue = float(v)

    @staticmethod
    def createByReal(v):
        return ValueInput(v)


class DocumentTypes:
    FusionDesignDocumentType = 0


class _UI:
    def messageBox(self, text, *a):
        print("[messageBox]", text)
        return 0


class _Document:
    def __init__(self, app, design):
        self.app, self.design = app, design

    def close(self, save):
        self.app._closed.append(self.design)
        return True


class _Documents:
    def __init__(self, app):
        self.app = app

    def add(self, t):
        from . import fusion
        d = fusion.Design()
        self.app.activeProduct = d
        self.app._designs.append(d)
        return _Document(self.app, d)


class Application:
    _app = None

    def __init__(self):
        self.userInterface = _UI()
        self.documents = _Documents(self)
        self.activeProduct = None
        self._designs, self._closed = [], []

    @staticmethod
    def get():
        if Application._app is None:
            Application._app = Application()
        return Application._app
