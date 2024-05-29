from apis.index import blueprint as index_blueprint
from apis.cdn import blueprint as cdn_blueprint

blueprints = [
    (index_blueprint, "/"),
    (cdn_blueprint, "/cdn"),
]
