from flask import Flask
from decouple import AutoConfig

config = AutoConfig(search_path='/app')

flask_app = Flask(__name__)
flask_app.config.from_object("core.settings")


def routes_initialize():
    """Initialize routes"""
    from core.urls import blueprints

    for bp in blueprints:
        flask_app.register_blueprint(bp[0], url_prefix=bp[1])
    
    # if config("DEBUG", cast=bool) or True:
    #     from flask_swagger_ui import get_swaggerui_blueprint

    #     SWAGGER_URL="/swagger"
    #     swagger_ui_blueprint = get_swaggerui_blueprint(
    #         SWAGGER_URL,
    #         "/static/swagger.json",
    #         config={
    #             'app_name': 'Sugarcane API'
    #         }
    #     )
    #     flask_app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    return flask_app


routes_initialize()